"""Pinned full BGE-M3 ONNX inference and exact-artifact qualification."""

from __future__ import annotations

import hashlib
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.conf import settings
from pydantic import BaseModel, ConfigDict, Field, model_validator

BGE_MODEL_NAME = "BAAI/bge-m3"
BGE_MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
BGE_SOURCE_BASE_URL = f"https://huggingface.co/BAAI/bge-m3/resolve/{BGE_MODEL_REVISION}/onnx"
BGE_DIMENSIONS = 1024
MIN_QUALIFICATION_CASES = 50
MIN_NDCG_AT_10 = 0.95
MIN_TOP_10_OVERLAP = 0.90
POLICY_INDEX_SCHEMA_VERSION = "bge-m3-fp32-onnx-1024+postgres-gin/1"
BGE_RUNTIME_PROFILE = "dense-fp32-onnx"


class RankingCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ndcg_at_10: float = Field(ge=0, le=1)
    top_10_overlap: float = Field(ge=0, le=1)


class ReferencePassage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=1, max_length=20_000)


class ReferenceCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=4_000)
    full_model_ranking: list[str] = Field(min_length=10)


class FullModelReferenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    model_name: str
    passages: list[ReferencePassage] = Field(min_length=10)
    cases: list[ReferenceCase] = Field(min_length=50)


class SourceArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remote_name: str
    local_name: str
    byte_count: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class BgeM3ArtifactManifestV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    model_id: str
    source_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    source_base_url: str
    profile: str
    onnx_version: str
    onnxruntime_version: str
    source_artifacts: list[SourceArtifactRecord]

    @model_validator(mode="after")
    def artifact_is_the_approved_build(self) -> BgeM3ArtifactManifestV1:
        artifacts = {item.remote_name: item for item in self.source_artifacts}
        expected_local_names = {
            "model.onnx": "source/model.onnx",
            "model.onnx_data": "source/model.onnx_data",
            "tokenizer.json": "tokenizer.json",
            "config.json": "source/config.json",
        }
        if (
            self.schema_version != 1
            or self.model_id != BGE_MODEL_NAME
            or self.source_revision != BGE_MODEL_REVISION
            or self.source_base_url != BGE_SOURCE_BASE_URL
            or self.profile != BGE_RUNTIME_PROFILE
            or self.onnx_version != "1.22.0"
            or self.onnxruntime_version != "1.30.0"
            or len(self.source_artifacts) != 4
            or set(artifacts) != set(expected_local_names)
            or any(
                artifacts[name].local_name != local_name
                for name, local_name in expected_local_names.items()
            )
        ):
            raise ValueError("BGE-M3 artifact manifest does not match the approved pinned build.")
        return self


class BgeM3QualificationV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    model_name: str
    representation: str
    dimensions: int
    source_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    artifact_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    onnx_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    external_weights_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    tokenizer_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    config_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    embedding_batch_size: int = Field(ge=1)
    normalization_max_error: float = Field(ge=0)
    case_results: list[RankingCaseResult]
    mean_ndcg_at_10: float = Field(ge=0, le=1)
    mean_top_10_overlap: float = Field(ge=0, le=1)
    passed: bool

    @model_validator(mode="after")
    def qualification_is_sufficient(self) -> BgeM3QualificationV1:
        expected_pass = (
            self.schema_version == 1
            and self.model_name == BGE_MODEL_NAME
            and self.source_revision == BGE_MODEL_REVISION
            and self.representation == BGE_RUNTIME_PROFILE
            and self.dimensions == BGE_DIMENSIONS
            and self.embedding_batch_size == 1
            and self.normalization_max_error <= 1e-5
            and len(self.case_results) >= MIN_QUALIFICATION_CASES
            and min(item.ndcg_at_10 for item in self.case_results) >= MIN_NDCG_AT_10
            and min(item.top_10_overlap for item in self.case_results) >= MIN_TOP_10_OVERLAP
            and self.mean_ndcg_at_10 >= MIN_NDCG_AT_10
            and self.mean_top_10_overlap >= MIN_TOP_10_OVERLAP
        )
        if self.passed != expected_pass:
            raise ValueError("BGE-M3 qualification result does not match the fixed gates.")
        return self


def policy_index_version(qualification: BgeM3QualificationV1) -> str:
    """Bind stored chunk vectors to exact model and tokenizer bytes."""

    artifact_identity = hashlib.sha256(
        (
            f"{qualification.onnx_sha256}:{qualification.external_weights_sha256}:"
            f"{qualification.tokenizer_sha256}:{qualification.config_sha256}"
        ).encode()
    ).hexdigest()
    return f"{POLICY_INDEX_SCHEMA_VERSION}:{artifact_identity}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def embedding_paths() -> tuple[Path, Path, Path, Path, Path]:
    model_root = Path(settings.COVERGUIDE_EMBEDDING_MODEL_PATH).resolve()
    qualification_path = Path(settings.COVERGUIDE_EMBEDDING_QUALIFICATION_PATH).resolve()
    return (
        model_root / "source/model.onnx",
        model_root / "source/model.onnx_data",
        model_root / "tokenizer.json",
        model_root / "source/config.json",
        qualification_path,
    )


def artifact_manifest_path() -> Path:
    return Path(settings.COVERGUIDE_EMBEDDING_MODEL_PATH).resolve() / "artifact-manifest.json"


type ArtifactFingerprint = tuple[tuple[str, int, int, int, int, int], ...]


def _artifact_fingerprint(paths: tuple[Path, ...]) -> ArtifactFingerprint:
    return tuple(
        (
            str(path),
            item.st_size,
            item.st_mtime_ns,
            item.st_ctime_ns,
            item.st_ino,
            item.st_dev,
        )
        for path in paths
        for item in (path.stat(),)
    )


@lru_cache(maxsize=8)
def _qualified_embedding_status_cached(
    fingerprint: ArtifactFingerprint,
) -> tuple[bool, str, BgeM3QualificationV1 | None]:
    (
        model_path,
        external_weights_path,
        tokenizer_path,
        config_path,
        manifest_path,
        qualification_path,
    ) = (Path(item[0]) for item in fingerprint)
    try:
        manifest = BgeM3ArtifactManifestV1.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        qualification = BgeM3QualificationV1.model_validate_json(
            qualification_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        return False, f"BGE-M3 qualification is invalid: {exc}", None
    records = {item.remote_name: item for item in manifest.source_artifacts}
    runtime_artifacts = (
        ("model.onnx", model_path, qualification.onnx_sha256),
        (
            "model.onnx_data",
            external_weights_path,
            qualification.external_weights_sha256,
        ),
        ("tokenizer.json", tokenizer_path, qualification.tokenizer_sha256),
        ("config.json", config_path, qualification.config_sha256),
    )
    for remote_name, path, qualified_sha256 in runtime_artifacts:
        record = records[remote_name]
        if sha256_file(path) != qualified_sha256:
            return (
                False,
                f"BGE-M3 {remote_name} bytes differ from the qualified artifact.",
                qualification,
            )
        if record.sha256 != qualified_sha256 or path.stat().st_size != record.byte_count:
            return (
                False,
                f"BGE-M3 build manifest identifies different {remote_name} bytes.",
                qualification,
            )
    if sha256_file(manifest_path) != qualification.artifact_manifest_sha256:
        return False, "BGE-M3 build manifest differs from the qualified artifact.", qualification
    if not qualification.passed:
        return False, "BGE-M3 ranking qualification did not pass.", qualification
    return True, "qualified", qualification


def qualified_embedding_status() -> tuple[bool, str, BgeM3QualificationV1 | None]:
    if not settings.COVERGUIDE_EMBEDDING_MODEL_PATH:
        return False, "COVERGUIDE_EMBEDDING_MODEL_PATH is not configured.", None
    if not settings.COVERGUIDE_EMBEDDING_QUALIFICATION_PATH:
        return False, "COVERGUIDE_EMBEDDING_QUALIFICATION_PATH is not configured.", None
    model_path, external_weights_path, tokenizer_path, config_path, qualification_path = (
        embedding_paths()
    )
    manifest_path = artifact_manifest_path()
    paths = (
        model_path,
        external_weights_path,
        tokenizer_path,
        config_path,
        manifest_path,
        qualification_path,
    )
    for path in paths:
        if not path.is_file():
            return False, f"Required BGE-M3 artifact is missing: {path.name}.", None
    try:
        fingerprint = _artifact_fingerprint(paths)
    except OSError as exc:
        return False, f"BGE-M3 qualification is invalid: {exc}", None
    return _qualified_embedding_status_cached(fingerprint)


def _dense_vectors_from_onnx(output: Any) -> Any:
    """Use BGE-M3's normalized CLS representation, never mean pooling."""

    import numpy as np

    vectors = np.asarray(output, dtype=np.float32)
    if vectors.ndim == 3:
        vectors = vectors[:, 0, :]
    if vectors.ndim != 2 or vectors.shape[1] != BGE_DIMENSIONS:
        raise RuntimeError("BGE-M3 ONNX output is not a 1024-dimensional dense representation.")
    return vectors


def _embedding_runtime_fingerprint(model_path: Path, tokenizer_path: Path) -> ArtifactFingerprint:
    external_data = model_path.with_name(model_path.name + "_data")
    paths = (
        (model_path, tokenizer_path, external_data)
        if external_data.is_file()
        else (model_path, tokenizer_path)
    )
    return _artifact_fingerprint(paths)


@lru_cache(maxsize=1)
def _embedding_runtime_cached(
    fingerprint: ArtifactFingerprint,
) -> tuple[Any, Any, frozenset[str]]:
    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer
    except ImportError as exc:
        raise RuntimeError("Pinned ONNX embedding runtime is not installed.") from exc
    model_path = Path(fingerprint[0][0])
    tokenizer_path = Path(fingerprint[1][0])
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.enable_truncation(max_length=512)
    tokenizer.enable_padding()
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    available = frozenset(item.name for item in session.get_inputs())
    return tokenizer, session, available


def embed_texts_from_onnx(
    model_path: Path,
    tokenizer_path: Path,
    texts: list[str],
    *,
    batch_size: int = 1,
) -> list[list[float]]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Pinned ONNX embedding runtime is not installed.") from exc
    if batch_size < 1:
        raise ValueError("Embedding batch size must be positive.")
    if not texts:
        return []
    try:
        fingerprint = _embedding_runtime_fingerprint(model_path, tokenizer_path)
    except OSError as exc:
        raise RuntimeError(f"Pinned ONNX embedding artifact is unavailable: {exc}") from exc
    tokenizer, session, available = _embedding_runtime_cached(fingerprint)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        encodings = tokenizer.encode_batch(texts[start : start + batch_size])
        input_ids = np.asarray([item.ids for item in encodings], dtype=np.int64)
        attention_mask = np.asarray([item.attention_mask for item in encodings], dtype=np.int64)
        inputs: dict[str, Any] = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }
        if "token_type_ids" in available:
            inputs["token_type_ids"] = np.zeros_like(input_ids)
        outputs = session.run(
            None, {key: value for key, value in inputs.items() if key in available}
        )
        dense = _dense_vectors_from_onnx(outputs[0])
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        dense = dense / np.maximum(norms, np.finfo(np.float32).eps)
        vectors.extend([[float(value) for value in row] for row in dense])
    return vectors


def _embed_texts_unchecked(texts: list[str]) -> list[list[float]]:
    model_path, _external_weights_path, tokenizer_path, _config_path, _qualification = (
        embedding_paths()
    )
    return embed_texts_from_onnx(model_path, tokenizer_path, texts, batch_size=1)


def embed_texts(texts: list[str]) -> list[list[float]]:
    ok, reason, _qualification = qualified_embedding_status()
    if not ok:
        raise RuntimeError(reason)
    return _embed_texts_unchecked(texts)


def embed_texts_for_qualification(texts: list[str]) -> list[list[float]]:
    """Run pinned local artifacts before a qualification document exists."""

    model_path, _external_weights_path, tokenizer_path, _config_path, _qualification = (
        embedding_paths()
    )
    if not model_path.is_file() or not tokenizer_path.is_file():
        raise RuntimeError("Pinned full BGE-M3 graph or tokenizer is missing.")
    return _embed_texts_unchecked(texts)


def ndcg_at_10(expected: list[str], observed: list[str]) -> float:
    relevant = {item: len(expected) - index for index, item in enumerate(expected[:10])}
    ideal = sum(
        relevance / math.log2(index + 2)
        for index, relevance in enumerate(sorted(relevant.values(), reverse=True))
    )
    if ideal == 0:
        return 1.0
    score = sum(
        relevant.get(identifier, 0) / math.log2(index + 2)
        for index, identifier in enumerate(observed[:10])
    )
    return score / ideal


def qualification_document(
    *,
    reference_sha256: str,
    cases: list[tuple[str, list[str], list[str]]],
    normalization_max_error: float,
) -> BgeM3QualificationV1:
    model_path, external_weights_path, tokenizer_path, config_path, _qualification = (
        embedding_paths()
    )
    manifest_path = artifact_manifest_path()
    manifest = BgeM3ArtifactManifestV1.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    results = [
        RankingCaseResult(
            query_sha256=hashlib.sha256(query.encode()).hexdigest(),
            ndcg_at_10=ndcg_at_10(expected, observed),
            top_10_overlap=(
                len(set(expected[:10]) & set(observed[:10])) / max(1, len(expected[:10]))
            ),
        )
        for query, expected, observed in cases
    ]
    mean_ndcg = sum(item.ndcg_at_10 for item in results) / max(1, len(results))
    mean_overlap = sum(item.top_10_overlap for item in results) / max(1, len(results))
    passed = (
        len(results) >= MIN_QUALIFICATION_CASES
        and normalization_max_error <= 1e-5
        and min((item.ndcg_at_10 for item in results), default=0) >= MIN_NDCG_AT_10
        and min((item.top_10_overlap for item in results), default=0) >= MIN_TOP_10_OVERLAP
        and mean_ndcg >= MIN_NDCG_AT_10
        and mean_overlap >= MIN_TOP_10_OVERLAP
    )
    return BgeM3QualificationV1(
        schema_version=1,
        model_name=BGE_MODEL_NAME,
        representation=BGE_RUNTIME_PROFILE,
        dimensions=BGE_DIMENSIONS,
        source_revision=manifest.source_revision,
        artifact_manifest_sha256=sha256_file(manifest_path),
        onnx_sha256=sha256_file(model_path),
        external_weights_sha256=sha256_file(external_weights_path),
        tokenizer_sha256=sha256_file(tokenizer_path),
        config_sha256=sha256_file(config_path),
        reference_sha256=reference_sha256,
        embedding_batch_size=1,
        normalization_max_error=normalization_max_error,
        case_results=results,
        mean_ndcg_at_10=mean_ndcg,
        mean_top_10_overlap=mean_overlap,
        passed=passed,
    )
