import json
from pathlib import Path

import jsonschema


def test_microtask_example_matches_schema() -> None:
    schema = json.loads(Path("schemas/microtask-packet-v1.json").read_text(encoding="utf-8"))
    example = json.loads(Path("examples/microtask-packet.example.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(example)


def test_graph_schemas_are_fail_closed() -> None:
    for name in ("graph-node-v1.json", "graph-edge-v1.json"):
        schema = json.loads(Path("schemas", name).read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False
        jsonschema.Draft202012Validator.check_schema(schema)
