"""Pinned local-model qualification manifests."""

from __future__ import annotations

from pathlib import Path

from .records import decode_json, record, string, strings

SHA256_HEX_LENGTH = 64


REQUIRED = {
    "schema_version",
    "model_id",
    "source_repository",
    "revision",
    "artifact",
    "sha256",
    "runtime",
    "task_classes",
    "benchmark_receipts",
}


def load_model_manifest(path: str | Path) -> dict[str, object]:
    """Validate a model manifest without inferring benchmark success.

    Returns:
        The validated manifest; benchmark receipts remain separate evidence.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    value = record(decode_json(Path(path).read_text(encoding="utf-8")))
    missing = sorted(REQUIRED - set(value))
    if missing:
        message = f"model manifest missing fields: {missing}"
        raise ValueError(message)
    if value["schema_version"] != "1.0":
        message = "unsupported model manifest schema"
        raise ValueError(message)
    digest = string(value["sha256"])
    if len(digest) != SHA256_HEX_LENGTH or any(
        ch not in "0123456789abcdef" for ch in digest
    ):
        message = "model sha256 must be lowercase hex"
        raise ValueError(message)
    if not strings(value["task_classes"]):
        message = "model manifest must declare at least one task class"
        raise ValueError(message)
    return value
