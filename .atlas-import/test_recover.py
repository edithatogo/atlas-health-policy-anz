"""Run with unittest, independent of application runtime qualification."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("recover", HERE / "recover.py")
recover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recover)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "transport"
        self.root.mkdir()
        shutil.copy(HERE / "manifest.json", self.root / "manifest.json")
        shutil.copytree(HERE / "parts", self.root / "parts")

    def test_exact_stream(self):
        stream = recover.verify_transport(self.root)
        self.assertEqual(hashlib.sha256(stream).hexdigest(), recover.STREAM)
        self.assertEqual(len(stream), 1053296)

    def test_wrong_size(self):
        with (self.root / "parts/030.b64").open("ab") as f:
            f.write(b"extra")
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_tamper(self):
        p = self.root / "parts/030.b64"
        p.write_bytes(b"A" + p.read_bytes()[1:])
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_missing(self):
        (self.root / "parts/031.b64").unlink()
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_extra(self):
        (self.root / "parts/032.b64").write_text("junk")
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_reordered(self):
        p = self.root / "manifest.json"
        manifest = json.loads(p.read_text())
        manifest["parts"].reverse()
        p.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_traversal(self):
        p = self.root / "manifest.json"
        manifest = json.loads(p.read_text())
        manifest["parts"][0]["name"] = "../secret"
        p.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_symlink(self):
        p = self.root / "parts/031.b64"
        outside = Path(self.temp.name) / "outside"
        shutil.move(p, outside)
        p.symlink_to(outside)
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_duplicate_manifest_key(self):
        p = self.root / "manifest.json"
        p.write_text(p.read_text().replace('{', '{"schema_version": 1,', 1))
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_wrong_stream_anchor(self):
        p = self.root / "manifest.json"
        p.write_text(p.read_text().replace(recover.STREAM, "0" * 64))
        with self.assertRaises(ValueError):
            recover.verify_transport(self.root)

    def test_part_hash_cannot_override_whole_anchor(self):
        p = self.root / "parts/030.b64"
        p.write_bytes(b"A" + p.read_bytes()[1:])
        m = self.root / "manifest.json"
        manifest = json.loads(m.read_text())
        manifest["parts"][29]["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        m.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "Compressed payload"):
            recover.verify_transport(self.root)

    def test_wrong_branch_blocks_restore(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": recover.REPOSITORY, "GITHUB_REF": "refs/heads/main"}):
            with self.assertRaisesRegex(ValueError, "Wrong workflow branch"):
                recover.restore(self.root, b"")


if __name__ == "__main__":
    unittest.main()
