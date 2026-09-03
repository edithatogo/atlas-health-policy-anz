from pathlib import Path

from australian_health_policy_atlas.offline_bundle import build_bundle, verify_bundle


def test_offline_bundle_detects_tampering(tmp_path: Path) -> None:
    source = tmp_path / "model.manifest.json"
    source.write_text("{}", encoding="utf-8")
    bundle = tmp_path / "bundle"
    build_bundle(files=[source], output_dir=bundle, bundle_id="b1")
    assert verify_bundle(bundle)[0]
    (bundle / "payload" / source.name).write_text("tampered", encoding="utf-8")
    ok, failures = verify_bundle(bundle)
    assert not ok
    assert failures[0].startswith("sha256_mismatch")
