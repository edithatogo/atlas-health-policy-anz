from pathlib import Path

from australian_health_policy_atlas.local_runner import prepare_local_document


def test_local_preparation_uses_no_network(tmp_path: Path) -> None:
    path = tmp_path / "policy.txt"
    path.write_text("A nurse must escalate care within 30 minutes.", encoding="utf-8")
    receipt = prepare_local_document(
        path, source_id="local", output_dir=tmp_path / "out"
    )
    assert receipt["network_used"] is False
    assert receipt["gold_candidate_count"] == 1
