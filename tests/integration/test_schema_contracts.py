from pathlib import Path

import jsonschema

from australian_health_policy_atlas.records import decode_json, record


def test_microtask_example_matches_schema() -> None:
    schema = record(
        decode_json(
            Path("schemas/microtask-packet-v1.json").read_text(encoding="utf-8")
        )
    )
    example = record(
        decode_json(
            Path("examples/microtask-packet.example.json").read_text(encoding="utf-8")
        )
    )
    jsonschema.validate(example, schema, cls=jsonschema.Draft202012Validator)


def test_graph_schemas_are_fail_closed() -> None:
    for name in ("graph-node-v1.json", "graph-edge-v1.json"):
        schema = record(decode_json(Path("schemas", name).read_text(encoding="utf-8")))
        assert schema["additionalProperties"] is False
        jsonschema.Draft202012Validator.check_schema(schema)
