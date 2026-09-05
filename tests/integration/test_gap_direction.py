import json

from australian_health_policy_atlas.domain import EvidenceState, PolicyAssertion
from australian_health_policy_atlas.gap import build_gap_rows
from australian_health_policy_atlas.institutional import run_institutional_gap_analysis


def test_absent_reference_requirement_is_not_silently_omitted(tmp_path):
    local = tmp_path / "local.txt"
    local.write_text("Nurses must document care.\n")
    base = tmp_path / "gold.jsonl"
    records = [
        dict(
            assertion_id="state-document",
            jurisdiction="QLD",
            source_id="state",
            source_span_id="span1",
            actor="Nurses",
            action="document",
            object="care",
            modality="must",
            evidence_state="A0",
        ),
        dict(
            assertion_id="state-escalate",
            jurisdiction="QLD",
            source_id="state",
            source_span_id="span2",
            actor="Doctors",
            action="escalate",
            object="deterioration",
            modality="must",
            evidence_state="A0",
        ),
    ]
    base.write_text("".join(json.dumps(row) + "\n" for row in records))
    out = tmp_path / "out"
    receipt = run_institutional_gap_analysis(
        local_document=local,
        local_source_id="local",
        public_gold_jsonl=base,
        output_dir=out,
    )
    rows = [
        json.loads(line) for line in (out / "gap-matrix.jsonl").read_text().splitlines()
    ]
    assert len(rows) == 2
    assert {row["reference_assertion_id"] for row in rows} == {
        "state-document",
        "state-escalate",
    }
    missing = next(
        row for row in rows if row["reference_assertion_id"] == "state-escalate"
    )
    assert missing["relationship"] == "no_candidate_found"
    assert missing["evidence_state"] == "A3"
    assert receipt["coverage_denominator"] == "reference_assertion_count"
    assert (
        len((out / "local-to-reference-candidates.jsonl").read_text().splitlines()) == 1
    )


def test_uncertainty_cannot_be_laundered_through_similarity():
    left = PolicyAssertion(
        "a",
        "QLD",
        "s",
        "sp",
        "nurse",
        "must",
        "document",
        "care",
        evidence_state=EvidenceState.NOT_DETERMINED,
    )
    right = PolicyAssertion(
        "b",
        "NSW",
        "t",
        "sq",
        "nurse",
        "must",
        "document",
        "care",
        evidence_state=EvidenceState.VERIFIED,
    )
    row = build_gap_rows([left], [right])[0]
    assert row.relationship == "not_determined"
    assert row.evidence_state == EvidenceState.NOT_DETERMINED
