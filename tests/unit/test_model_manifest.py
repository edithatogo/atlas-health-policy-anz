from australian_health_policy_atlas.model_manifest import load_model_manifest


def test_example_model_manifest_contract() -> None:
    value = load_model_manifest("examples/model-manifest.example.json")
    assert value["runtime"] == "llama.cpp"
