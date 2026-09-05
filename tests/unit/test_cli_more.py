import json
from pathlib import Path

from australian_health_policy_atlas.cli import main


def test_cli_modality_and_prepare_local(tmp_path: Path, capsys: object) -> None:
    assert main(["classify-modality", "Nurse may act."]) == 0
    path = tmp_path / "x.txt"
    path.write_text("Nurse may act.", encoding="utf-8")
    assert (
        main([
            "prepare-local",
            str(path),
            "--source-id",
            "x",
            "--output-dir",
            str(tmp_path / "out"),
        ])
        == 0
    )


def test_cli_bundle_build_and_verify(tmp_path: Path, capsys: object) -> None:
    payload = tmp_path / "baseline.jsonl"
    payload.write_text("{}\n", encoding="utf-8")
    bundle = tmp_path / "bundle"
    assert (
        main([
            "bundle-build",
            "--output-dir",
            str(bundle),
            "--bundle-id",
            "b1",
            str(payload),
        ])
        == 0
    )
    assert main(["bundle-verify", str(bundle)]) == 0
    (bundle / "payload" / payload.name).write_text("changed\n", encoding="utf-8")
    assert main(["bundle-verify", str(bundle)]) == 1


def test_cli_institutional_gap(tmp_path: Path, capsys: object) -> None:
    local = tmp_path / "local.txt"
    local.write_text("The nurse must review the patient.", encoding="utf-8")
    baseline = tmp_path / "gold.jsonl"
    baseline.write_text(
        json.dumps({
            "assertion_id": "qld-1",
            "jurisdiction": "QLD",
            "source_id": "qld.policy",
            "source_span_id": "span-1",
            "actor": "nurse",
            "modality": "must",
            "action": "review",
            "object": "the patient",
            "authority_type": "policy",
            "evidence_state": "A0",
            "reason_codes": ["fixture"],
        })
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "gap"
    assert (
        main([
            "institutional-gap",
            str(local),
            str(baseline),
            "--source-id",
            "local-1",
            "--output-dir",
            str(output),
        ])
        == 0
    )
    assert (output / "institutional-gap-receipt.json").exists()
