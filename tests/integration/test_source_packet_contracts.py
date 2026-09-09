"""Exercise the committed original-byte packet without fetching or interpreting PDFs."""

from pathlib import Path

import jsonschema
import pytest

from australian_health_policy_atlas.hashing import sha256_file
from australian_health_policy_atlas.integrity import read_json
from australian_health_policy_atlas.packet_ingestion import (
    inspect_packet,
    load_packet_registry,
)
from australian_health_policy_atlas.packet_staging import build_packet_stage
from australian_health_policy_atlas.records import records
from tests.packet_support import packet_fixture


def test_actual_committed_originals_preserve_finite_failure_denominator() -> None:
    spec = load_packet_registry(Path())[0]
    root = Path(spec.directory)
    result = inspect_packet(root, spec)
    assert result["source_count"] == 15
    assert result["captured_count"] == result["unique_object_count"] == 8
    assert result["failed_count"] == 7
    assert result["total_unique_bytes"] == 17390153
    assert len(records(result["objects"])) == 8
    assert not result["acquisition_complete"]
    assert not result["gate_b_passed"]
    assert sha256_file(root / "request.json") == spec.request_sha256


def test_packet_registry_and_staging_schemas(tmp_path: Path) -> None:
    fixture = packet_fixture(tmp_path)
    manifest = build_packet_stage(fixture.root, fixture.spec, tmp_path / "stage")
    for filename, example in (
        (
            "source-packet-registry-v1.json",
            read_json(Path("data/sources/source-packets-v1.json").read_bytes()),
        ),
        ("source-packet-staging-v1.json", manifest),
    ):
        schema = read_json(Path("schemas", filename).read_bytes())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(example, schema, cls=jsonschema.Draft202012Validator)
    manifest["gate_b_passed"] = True
    with pytest.raises(jsonschema.ValidationError, match="False was expected"):
        jsonschema.validate(manifest, schema, cls=jsonschema.Draft202012Validator)
