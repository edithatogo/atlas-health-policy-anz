from australian_health_policy_atlas.source_registry import load_registry


def test_seed_registry_has_all_state_and_territory_jurisdictions() -> None:
    registry = load_registry("data/sources/jurisdictions-v1.json")
    jurisdictions = {item["jurisdiction"] for item in registry["sources"]}
    assert jurisdictions == {"ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"}
