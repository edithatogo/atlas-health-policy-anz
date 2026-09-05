"""Concrete types and JSON syntax cannot substitute for evidence validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from australian_health_policy_atlas import records as r
from australian_health_policy_atlas.graph import PolicyGraph, load_graph
from australian_health_policy_atlas.graphrag import retrieve_graph_context
from australian_health_policy_atlas.hashing import sha256_json
from australian_health_policy_atlas.integrity import read_json
from australian_health_policy_atlas.local_runner import prepare_local_document


@pytest.mark.parametrize("value", [None, [], 1, True, "{}"])
def test_record_rejects_non_objects(value: object) -> None:
    with pytest.raises(TypeError, match="JSON object required"):
        r.record(value)


def test_record_rejects_non_string_keys() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        r.record({1: "not a string key"})


@pytest.mark.parametrize("value", [None, {}, (), "[]"])
def test_array_rejects_non_lists(value: object) -> None:
    with pytest.raises(TypeError, match="JSON array required"):
        r.array(value)


@pytest.mark.parametrize("value", [None, 1, True, []])
def test_string_never_coerces(value: object) -> None:
    with pytest.raises(TypeError, match="string required"):
        r.string(value)


@pytest.mark.parametrize("value", [True, False, 1.5, "3", None])
def test_integer_rejects_booleans_and_coercions(value: object) -> None:
    with pytest.raises(TypeError, match="integer required"):
        r.integer(value)


@pytest.mark.parametrize("value", [True, False, "1.5", None])
def test_number_rejects_booleans_and_coercions(value: object) -> None:
    with pytest.raises(TypeError, match="number required"):
        r.number(value)


@pytest.mark.parametrize("value", [0, -3, 2.75])
def test_number_preserves_valid_numeric_values(value: float) -> None:
    assert r.number(value) == pytest.approx(value)


def test_validated_containers_preserve_mutation_identity() -> None:
    value: dict[str, object] = {"items": [{"state": "queued"}]}
    assert r.record(value) is value
    items = r.array(value["items"])
    assert r.array(items) is items
    rows = r.records(items)
    rows[0]["state"] = "captured"
    assert r.record(items[0])["state"] == "captured"
    assert rows is not items
    assert r.optional_string(None) is None
    assert r.optional_string("scope") == "scope"
    assert r.strings(["AU", "NZ"]) == ["AU", "NZ"]
    assert r.integer(0) == 0


@pytest.mark.parametrize("text", ["NaN", "Infinity", "-Infinity", "1e309", "-1e309"])
def test_non_finite_json_is_rejected_at_decoding(text: str) -> None:
    with pytest.raises(ValueError, match="non-finite JSON"):
        r.decode_json('{"value":' + text + "}")


def test_nested_duplicate_keys_are_not_silently_overwritten() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        r.decode_json('{"outer":{"value":1,"value":2}}')


def test_json_object_contract_preserves_value_error_boundary() -> None:
    with pytest.raises(ValueError, match="JSON object required"):
        read_json(b"[]")
    value = r.record(r.decode_json('{"valid": 1.5, "nested": [true, null]}'))
    assert r.number(value["valid"]) == pytest.approx(1.5)
    assert r.array(value["nested"]) == [True, None]
    assert sha256_json(value)


@pytest.mark.parametrize("hops", [-1, 9])
def test_graph_path_budget_cannot_be_negative_or_unbounded(hops: int) -> None:
    with pytest.raises(ValueError, match="zero to eight hops"):
        retrieve_graph_context(PolicyGraph(), "care", max_hops=hops)


@pytest.mark.parametrize("budget", [0, -1])
def test_graph_candidate_budget_must_be_positive(budget: int) -> None:
    with pytest.raises(ValueError, match="positive candidate budgets"):
        retrieve_graph_context(PolicyGraph(), "care", top_k=budget)
    with pytest.raises(ValueError, match="positive candidate budgets"):
        retrieve_graph_context(PolicyGraph(), "care", seed_k=budget)


def test_graph_boolean_budget_is_not_an_integer_budget() -> None:
    with pytest.raises(TypeError, match="budgets must be integers"):
        retrieve_graph_context(PolicyGraph(), "care", max_hops=True)


@pytest.mark.parametrize(
    ("text", "state"), [("Nurses must document care.", "A2"), ("Nurses must.", "A3")]
)
def test_local_candidates_and_graphs_cannot_claim_a0(
    tmp_path: Path, text: str, state: str
) -> None:
    path = tmp_path / "policy.txt"
    path.write_text(text, encoding="utf-8")
    output = tmp_path / "derived"
    receipt = prepare_local_document(
        path, source_id="local", output_dir=output, build_graph_projection=True
    )
    row = r.record(r.decode_json((output / "gold-candidates.jsonl").read_bytes()))
    assert row["evidence_state"] == state
    graph = load_graph(output / "graph")
    assertion = next(n for n in graph.nodes.values() if n.kind == "assertion")
    assert assertion.properties["evidence_state"] == state
    assert "extractor_not_qualified" in r.strings(assertion.properties["reason_codes"])
    assert receipt["network_used"] is False
