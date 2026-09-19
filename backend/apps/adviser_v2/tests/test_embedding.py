from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import ValidationError

from apps.adviser_v2.embedding import (
    BGE_DIMENSIONS,
    BGE_MODEL_REVISION,
    BGE_SOURCE_BASE_URL,
    BgeM3ArtifactManifestV1,
    BgeM3QualificationV1,
    _artifact_fingerprint,
    _dense_vectors_from_onnx,
    _embedding_runtime_cached,
    _embedding_runtime_fingerprint,
    _qualified_embedding_status_cached,
    policy_index_version,
)
from scripts.prepare_bge_m3 import (
    QuantizationProfile,
    SourceArtifact,
    ensure_headroom,
    quantize,
    quantized_nodes,
)


def test_bge_m3_uses_cls_token_instead_of_mean_pooling() -> None:
    output = np.zeros((1, 2, BGE_DIMENSIONS), dtype=np.float32)
    output[0, 0, :2] = [3.0, 4.0]
    output[0, 1, :2] = [100.0, 100.0]

    vectors = _dense_vectors_from_onnx(output)

    assert vectors.shape == (1, BGE_DIMENSIONS)
    assert vectors[0, :2].tolist() == [3.0, 4.0]


def test_policy_index_version_is_bound_to_exact_embedding_artifacts() -> None:
    first = BgeM3QualificationV1.model_construct(
        onnx_sha256="a" * 64,
        external_weights_sha256="d" * 64,
        tokenizer_sha256="b" * 64,
        config_sha256="e" * 64,
    )
    changed_model = BgeM3QualificationV1.model_construct(
        onnx_sha256="c" * 64,
        external_weights_sha256="d" * 64,
        tokenizer_sha256="b" * 64,
        config_sha256="e" * 64,
    )

    version = policy_index_version(first)

    assert version == policy_index_version(first)
    assert version != policy_index_version(changed_model)
    assert len(version) <= 160


def test_embedding_qualification_hashes_each_unchanged_artifact_set_once(
    tmp_path: Path,
) -> None:
    paths = tuple(
        tmp_path / name
        for name in (
            "model",
            "external-weights",
            "tokenizer",
            "config",
            "manifest",
            "qualification",
        )
    )
    for path in paths:
        path.write_text("{}", encoding="utf-8")
    fingerprint = _artifact_fingerprint(paths)
    _qualified_embedding_status_cached.cache_clear()

    first = _qualified_embedding_status_cached(fingerprint)
    second = _qualified_embedding_status_cached(fingerprint)

    assert first is second
    assert _qualified_embedding_status_cached.cache_info().hits == 1
    _qualified_embedding_status_cached.cache_clear()


def test_embedding_runtime_loads_each_unchanged_model_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model.int8.onnx"
    tokenizer_path = tmp_path / "tokenizer.json"
    model_path.write_bytes(b"model")
    tokenizer_path.write_text("{}", encoding="utf-8")
    loads = {"tokenizer": 0, "session": 0}

    class FakeTokenizer:
        @classmethod
        def from_file(cls, _path: str) -> FakeTokenizer:
            loads["tokenizer"] += 1
            return cls()

        def enable_truncation(self, *, max_length: int) -> None:
            assert max_length == 512

        def enable_padding(self) -> None:
            return None

    class FakeSession:
        def __init__(self, _path: str, *, providers: list[str]) -> None:
            loads["session"] += 1
            assert providers == ["CPUExecutionProvider"]

        def get_inputs(self) -> list[SimpleNamespace]:
            return [SimpleNamespace(name="input_ids"), SimpleNamespace(name="attention_mask")]

    monkeypatch.setitem(sys.modules, "tokenizers", SimpleNamespace(Tokenizer=FakeTokenizer))
    monkeypatch.setitem(sys.modules, "onnxruntime", SimpleNamespace(InferenceSession=FakeSession))
    fingerprint = _embedding_runtime_fingerprint(model_path, tokenizer_path)
    _embedding_runtime_cached.cache_clear()

    first = _embedding_runtime_cached(fingerprint)
    second = _embedding_runtime_cached(fingerprint)

    assert first is second
    assert loads == {"tokenizer": 1, "session": 1}
    _embedding_runtime_cached.cache_clear()


def full_runtime_manifest_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "model_id": "BAAI/bge-m3",
        "source_revision": BGE_MODEL_REVISION,
        "source_base_url": BGE_SOURCE_BASE_URL,
        "profile": "dense-fp32-onnx",
        "onnx_version": "1.22.0",
        "onnxruntime_version": "1.30.0",
        "source_artifacts": [
            {
                "remote_name": name,
                "local_name": {
                    "model.onnx": "source/model.onnx",
                    "model.onnx_data": "source/model.onnx_data",
                    "tokenizer.json": "tokenizer.json",
                    "config.json": "source/config.json",
                }[name],
                "byte_count": 1,
                "sha256": "a" * 64,
            }
            for name in ("model.onnx", "model.onnx_data", "tokenizer.json", "config.json")
        ],
    }


def test_bge_m3_build_manifest_is_closed_and_revision_pinned() -> None:
    payload = full_runtime_manifest_payload()

    assert BgeM3ArtifactManifestV1.model_validate(payload).source_revision == BGE_MODEL_REVISION
    payload["profile"] = "all-qint8"
    with pytest.raises(ValidationError):
        BgeM3ArtifactManifestV1.model_validate(payload)
    payload["profile"] = "dense-fp32-onnx"
    payload["source_revision"] = "0" * 40
    with pytest.raises(ValidationError):
        BgeM3ArtifactManifestV1.model_validate(payload)


def test_bge_m3_build_manifest_requires_external_weights() -> None:
    payload = full_runtime_manifest_payload()
    artifacts = payload["source_artifacts"]
    assert isinstance(artifacts, list)
    payload["source_artifacts"] = [
        item for item in artifacts if item["remote_name"] != "model.onnx_data"
    ]

    with pytest.raises(ValidationError):
        BgeM3ArtifactManifestV1.model_validate(payload)


def test_first_18_profile_leaves_final_encoder_layers_unquantized(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class Node:
        def __init__(self, name: str, op_type: str = "MatMul") -> None:
            self.name = name
            self.op_type = op_type

    class Graph:
        node = [
            Node("/encoder/layer.0/attention/MatMul"),
            Node("/encoder/layer.17/attention/MatMul"),
            Node("/encoder/layer.18/attention/MatMul"),
            Node("/encoder/layer.5/attention/Add", "Add"),
            Node("/pooler/MatMul"),
        ]

    class Model:
        graph = Graph()

    monkeypatch.setattr("onnx.load", lambda *_args, **_kwargs: Model())
    profile = QuantizationProfile("first-18-qint8", "QInt8", True, False, 0, 18)

    assert quantized_nodes(tmp_path / "model.onnx", profile) == [
        "/encoder/layer.0/attention/MatMul",
        "/encoder/layer.17/attention/MatMul",
    ]


def test_force_quantize_reserves_space_without_reclaiming_current_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "model"
    output_root = root / "candidate"
    output_root.mkdir(parents=True)
    (output_root / "model.int8.onnx").write_bytes(b"x" * 200)
    artifacts = (
        SourceArtifact("model.onnx", "source/model.onnx", 100, "a" * 64),
        SourceArtifact("model.onnx_data", "source/model.onnx_data", 200, "b" * 64),
        SourceArtifact("tokenizer.json", "tokenizer.json", 10, "c" * 64),
        SourceArtifact("config.json", "source/config.json", 5, "d" * 64),
    )
    monkeypatch.setattr("scripts.prepare_bge_m3.SOURCE_ARTIFACTS", artifacts)
    monkeypatch.setattr("scripts.prepare_bge_m3.verified", lambda *_args: True)
    monkeypatch.setattr("scripts.prepare_bge_m3.MINIMUM_POST_DOWNLOAD_HEADROOM", 1_000)
    monkeypatch.setattr(
        "scripts.prepare_bge_m3.shutil.disk_usage",
        lambda _path: SimpleNamespace(free=1_299),
    )

    with pytest.raises(RuntimeError, match="needs 1,300 additional free bytes"):
        ensure_headroom(
            root,
            output_root,
            download_only=False,
            force_quantize=True,
        )


def test_force_quantize_keeps_current_artifact_when_replacement_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import onnx
    import onnxruntime
    import onnxruntime.quantization

    root = tmp_path / "model"
    output_root = root / "candidate"
    (root / "source").mkdir(parents=True)
    output_root.mkdir()
    output = output_root / "model.int8.onnx"
    output.write_bytes(b"known-good-model")
    monkeypatch.setattr(onnx, "__version__", "1.22.0")
    monkeypatch.setattr(onnxruntime, "__version__", "1.30.0")

    def fail_quantization(**_kwargs: object) -> None:
        assert output.read_bytes() == b"known-good-model"
        raise RuntimeError("simulated quantizer failure")

    monkeypatch.setattr(onnxruntime.quantization, "quantize_dynamic", fail_quantization)
    profile = QuantizationProfile("all-qint8", "QInt8", True, False, None, None)

    with pytest.raises(RuntimeError, match="simulated quantizer failure"):
        quantize(root, output_root, profile, force=True)

    assert output.read_bytes() == b"known-good-model"
