#!/usr/bin/env python3
"""Download one pinned official BGE-M3 ONNX revision and support deferred experiments.

The script is intentionally fixed-source: it fetches only the listed files from one
reviewed Hugging Face revision, verifies exact byte counts and SHA-256 digests, and
never performs model discovery. The application loads the full ``source/model.onnx``
graph with its external weights. Quantization profiles remain available only for
explicit, deferred qualification experiments and are not a runtime contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import httpx

MODEL_ID = "BAAI/bge-m3"
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
BASE_URL = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/onnx"
MINIMUM_POST_DOWNLOAD_HEADROOM = 3_000_000_000


@dataclass(frozen=True)
class SourceArtifact:
    remote_name: str
    local_name: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class QuantizationProfile:
    name: str
    weight_type: str
    per_channel: bool
    reduce_range: bool
    layer_start: int | None
    layer_end: int | None


QUANTIZATION_PROFILES = {
    profile.name: profile
    for profile in (
        QuantizationProfile("all-qint8", "QInt8", True, False, None, None),
        QuantizationProfile("all-qint8-reduce-range", "QInt8", True, True, None, None),
        QuantizationProfile("last-12-qint8", "QInt8", True, False, 12, None),
        QuantizationProfile("last-6-qint8", "QInt8", True, False, 18, None),
        QuantizationProfile("first-18-qint8", "QInt8", True, False, 0, 18),
        QuantizationProfile("all-quint8", "QUInt8", True, False, None, None),
    )
}
LAYER_PATTERN = re.compile(r"/encoder/layer\.(\d+)/")


SOURCE_ARTIFACTS = (
    SourceArtifact(
        "model.onnx",
        "source/model.onnx",
        724_923,
        "f84251230831afb359ab26d9fd37d5936d4d9bb5d1d5410e66442f630f24435b",
    ),
    SourceArtifact(
        "model.onnx_data",
        "source/model.onnx_data",
        2_266_820_608,
        "1eebfb28493f67bba03ce0ef64bfdc7fc5a3bd9d7493f818bb1d78cd798416b4",
    ),
    SourceArtifact(
        "tokenizer.json",
        "tokenizer.json",
        17_082_821,
        "6710678b12670bc442b99edc952c4d996ae309a7020c1fa0096dd245c2faf790",
    ),
    SourceArtifact(
        "config.json",
        "source/config.json",
        698,
        "f24afd5de914fba8c668426c43d208a1a54022500c63b2c160be20891686fce8",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verified(path: Path, artifact: SourceArtifact) -> bool:
    return (
        path.is_file()
        and path.stat().st_size == artifact.byte_count
        and sha256_file(path) == artifact.sha256
    )


def ensure_headroom(
    root: Path,
    output_root: Path,
    *,
    download_only: bool,
    force_quantize: bool,
) -> None:
    missing_bytes = sum(
        artifact.byte_count
        for artifact in SOURCE_ARTIFACTS
        if not verified(root / artifact.local_name, artifact)
    )
    quantized_output = output_root / "model.int8.onnx"
    quantization_bytes = 0
    if not download_only and (force_quantize or not quantized_output.is_file()):
        quantization_bytes = sum(
            artifact.byte_count
            for artifact in SOURCE_ARTIFACTS
            if artifact.remote_name in {"model.onnx", "model.onnx_data"}
        )
    free_bytes = shutil.disk_usage(root.parent if root.parent.exists() else Path.cwd()).free
    required = missing_bytes + quantization_bytes + MINIMUM_POST_DOWNLOAD_HEADROOM
    if free_bytes < required:
        raise RuntimeError(
            f"Pinned BGE-M3 setup needs {required:,} additional free bytes including "
            "download, quantization, and safety headroom; "
            f"only {free_bytes:,} are available."
        )


def download(client: httpx.Client, root: Path, artifact: SourceArtifact) -> Path:
    destination = root / artifact.local_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if verified(destination, artifact):
        print(f"verified {artifact.local_name}")
        return destination
    if destination.exists():
        raise RuntimeError(f"Refusing to overwrite mismatched artifact: {destination}")
    partial = destination.with_suffix(destination.suffix + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > artifact.byte_count:
        raise RuntimeError(f"Partial artifact exceeds expected size: {partial}")
    headers = {"Range": f"bytes={offset}-"} if offset else {}
    mode = "ab" if offset else "wb"
    with client.stream("GET", f"{BASE_URL}/{artifact.remote_name}", headers=headers) as response:
        response.raise_for_status()
        if offset and response.status_code != 206:
            raise RuntimeError("Pinned artifact server did not honor the resume range.")
        with partial.open(mode) as handle:
            for chunk in response.iter_bytes(4 * 1024 * 1024):
                handle.write(chunk)
    if partial.stat().st_size != artifact.byte_count:
        raise RuntimeError(f"Downloaded byte count differs for {artifact.remote_name}.")
    if sha256_file(partial) != artifact.sha256:
        raise RuntimeError(f"Downloaded SHA-256 differs for {artifact.remote_name}.")
    os.replace(partial, destination)
    print(f"captured {artifact.local_name} ({artifact.byte_count:,} bytes)")
    return destination


def quantized_nodes(source: Path, profile: QuantizationProfile) -> list[str] | None:
    if profile.layer_start is None and profile.layer_end is None:
        return None
    import onnx

    graph = onnx.load(source, load_external_data=False)
    selected: list[str] = []
    for node in graph.graph.node:
        match = LAYER_PATTERN.search(node.name)
        if node.op_type not in {"MatMul", "Gemm"} or match is None:
            continue
        layer_number = int(match.group(1))
        if (profile.layer_start is None or layer_number >= profile.layer_start) and (
            profile.layer_end is None or layer_number < profile.layer_end
        ):
            selected.append(node.name)
    if not selected:
        raise RuntimeError(f"Quantization profile {profile.name} selected no ONNX nodes.")
    return selected


def quantize(
    root: Path,
    output_root: Path,
    profile: QuantizationProfile,
    *,
    force: bool,
) -> tuple[Path, int | None]:
    import onnx
    import onnxruntime
    from onnxruntime.quantization import QuantType, quantize_dynamic

    if onnxruntime.__version__ != "1.30.0":
        raise RuntimeError("Quantization requires the pinned onnxruntime 1.30.0.")
    if onnx.__version__ != "1.22.0":
        raise RuntimeError("Quantization requires the pinned onnx 1.22.0.")
    source = root / "source/model.onnx"
    output_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    output = output_root / "model.int8.onnx"
    temporary = output_root / ".model.int8.onnx.tmp"
    nodes = quantized_nodes(source, profile)
    if output.is_file():
        if not force:
            print(f"retaining existing quantized artifact {output}")
            return output, len(nodes) if nodes is not None else None
        print(f"preserving existing quantized artifact until replacement succeeds: {output}")
    temporary.unlink(missing_ok=True)
    quantize_dynamic(
        model_input=str(source),
        model_output=str(temporary),
        per_channel=profile.per_channel,
        reduce_range=profile.reduce_range,
        weight_type={"QInt8": QuantType.QInt8, "QUInt8": QuantType.QUInt8}[profile.weight_type],
        nodes_to_quantize=nodes,
        use_external_data_format=False,
        extra_options={"MatMulConstBOnly": True},
    )
    if not temporary.is_file() or temporary.stat().st_size == 0:
        raise RuntimeError("ONNX Runtime did not create a quantized model artifact.")
    os.replace(temporary, output)
    print(f"created model.int8.onnx ({output.stat().st_size:,} bytes)")
    return output, len(nodes) if nodes is not None else None


def write_manifest(
    root: Path,
    output_root: Path,
    quantized: Path,
    profile: QuantizationProfile,
    requested_node_count: int | None,
) -> None:
    import onnx
    import onnxruntime

    payload = {
        "schema_version": 1,
        "model_id": MODEL_ID,
        "source_revision": MODEL_REVISION,
        "source_base_url": BASE_URL,
        "source_artifacts": [
            {
                "remote_name": item.remote_name,
                "local_name": item.local_name,
                "byte_count": item.byte_count,
                "sha256": item.sha256,
            }
            for item in SOURCE_ARTIFACTS
        ],
        "quantization": {
            "profile": profile.name,
            "onnx_version": onnx.__version__,
            "onnxruntime_version": onnxruntime.__version__,
            "weight_type": profile.weight_type,
            "per_channel": profile.per_channel,
            "reduce_range": profile.reduce_range,
            "layer_start": profile.layer_start,
            "layer_end": profile.layer_end,
            "requested_node_count": requested_node_count,
            "use_external_data_format": False,
            "matmul_const_b_only": True,
        },
        "quantized_artifact": {
            "local_name": quantized.name,
            "byte_count": quantized.stat().st_size,
            "sha256": sha256_file(quantized),
        },
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tokenizer_source = root / "tokenizer.json"
    tokenizer_output = output_root / "tokenizer.json"
    if tokenizer_source != tokenizer_output:
        shutil.copyfile(tokenizer_source, tokenizer_output)
    temporary = output_root / ".artifact-manifest.json.tmp"
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, output_root / "artifact-manifest.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("data/v2/models/bge-m3-5617a9f6"),
    )
    parser.add_argument(
        "--profile",
        choices=sorted(QUANTIZATION_PROFILES),
        default="all-qint8",
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--force-quantize", action="store_true")
    parser.add_argument("--download-only", action="store_true")
    args = parser.parse_args()
    root = args.model_root.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    output_root = (args.output_root or root).resolve()
    ensure_headroom(
        root,
        output_root,
        download_only=args.download_only,
        force_quantize=args.force_quantize,
    )
    timeout = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=30.0)
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        for artifact in SOURCE_ARTIFACTS:
            download(client, root, artifact)
    if args.download_only:
        return
    profile = QUANTIZATION_PROFILES[args.profile]
    quantized, requested_node_count = quantize(
        root,
        output_root,
        profile,
        force=args.force_quantize,
    )
    write_manifest(root, output_root, quantized, profile, requested_node_count)


if __name__ == "__main__":
    main()
