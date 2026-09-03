import json
from pathlib import Path

import jsonschema


def test_microtask_example_matches_schema() -> None:
    schema = json.loads(Path("schemas/microtask-packet-v1.json").read_text(encoding="utf-8"))
    example = json.loads(Path("examples/microtask-packet.example.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(example)
