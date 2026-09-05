import json
from pathlib import Path

from australian_health_policy_atlas.offline_bundle import build_bundle, verify_bundle


def test_bundle_detects_manifest_and_missing_file(tmp_path: Path) -> None:
    src = tmp_path / "x"; src.write_text("x")
    root = tmp_path / "b"; build_bundle(files=[src], output_dir=root, bundle_id="id")
    manifest = json.loads((root / "bundle-manifest.json").read_text())
    manifest["bundle_id"] = "tampered"
    (root / "bundle-manifest.json").write_text(json.dumps(manifest))
    ok, failures = verify_bundle(root)
    assert not ok and "manifest_identity_mismatch" in failures

    # Restore by rebuilding, then delete a payload.
    build_bundle(files=[src], output_dir=root, bundle_id="id")
    (root / "payload" / "x").unlink()
    ok2, failures2 = verify_bundle(root)
    assert not ok2 and any(item.startswith("missing:") for item in failures2)
