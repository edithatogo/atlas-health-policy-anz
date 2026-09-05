"""T00: restore the exact recovered Atlas on the dedicated PR branch only."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SOURCE = "9cb1e709b8380dd71d35f22f866a02187119a3e2"
TREE = "a7211fdde23bafc254a10c52e755448b98665551"
COMPRESSED = "04ff28fd3fd6e24e1229d1892576ba0719a0ff2f343b6da5d27bf5e07894f792"
STREAM = "cd77df821aaeec1371a48ab8c93a6d7a133645f51b6c109205aef39f1b9e1d96"
REPOSITORY = "edithatogo/atlas-health-policy-anz"
BRANCH = "fix/complete-atlas-import"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate manifest key: " + key)
        result[key] = value
    return result


def verify_transport(root: Path) -> bytes:
    """Verify declared parts and independent immutable whole-payload anchors."""
    manifest_path = root / "manifest.json"
    require(not root.is_symlink() and not manifest_path.is_symlink(), "Symlinked transport")
    require(manifest_path.stat().st_size < 20000, "Oversized manifest")
    manifest = json.loads(manifest_path.read_text(), object_pairs_hook=unique_object)
    expected = {"schema_version": 1, "source_commit": SOURCE, "source_tree": TREE,
                "compressed_sha256": COMPRESSED, "compressed_bytes": 136028,
                "stream_bytes": 1053296, "stream_sha256": STREAM}
    for key, value in expected.items():
        require(type(manifest.get(key)) is type(value) and manifest[key] == value,
                "Unexpected transport identity: " + key)
    names = [f"{i:03d}.b64" for i in range(1, 32)]
    entries = manifest.get("parts")
    require(isinstance(entries, list) and len(entries) == len(names), "Wrong part count")
    directory = root / "parts"
    require(not directory.is_symlink(), "Symlinked parts directory")
    require(sorted(p.name for p in directory.iterdir()) == names, "Part inventory mismatch")
    chunks = []
    for index, (name, entry) in enumerate(zip(names, entries, strict=True)):
        require(isinstance(entry, dict) and entry.get("name") == name, "Unsafe/reordered part")
        size = 6001 if index < 30 else 1373
        path = directory / name
        require(path.is_file() and not path.is_symlink(), "Unsafe part: " + name)
        require(type(entry.get("bytes")) is int and entry["bytes"] == size,
                "Wrong declared part size: " + name)
        require(path.stat().st_size == size, "Wrong part size: " + name)
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == entry.get("sha256"), "Part hash: " + name)
        require(data.endswith(b"\n") and b"\n" not in data[:-1], "Part framing: " + name)
        chunks.append(data[:-1])
    compressed = base64.b64decode(b"".join(chunks), validate=True)
    require(len(compressed) == 136028 and hashlib.sha256(compressed).hexdigest() == COMPRESSED,
            "Compressed payload identity mismatch")
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    stream = decoder.decompress(compressed, max_length=1053297)
    require(decoder.eof and not decoder.unused_data and len(stream) == 1053296,
            "Decompression length/framing mismatch")
    require(hashlib.sha256(stream).hexdigest() == STREAM, "Stream identity mismatch")
    return stream


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], input=input_bytes,
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def source_inventory(repo: Path) -> list[tuple[str, str, str]]:
    rows = []
    for row in git(repo, "ls-tree", "-r", "-z", SOURCE).split(b"\0"):
        if row:
            metadata, path = row.split(b"\t", 1)
            mode, kind, sha = metadata.decode().split()
            require(kind == "blob" and mode in ("100644", "100755"), "Unsafe source entry")
            rows.append((mode, sha, path.decode()))
    require(len(rows) == 252, "Unexpected source inventory")
    return rows


def restore(repo: Path, stream: bytes) -> dict[str, object]:
    """Preserve both histories; never push or mutate a default branch."""
    require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY, "Wrong repository")
    require(os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH, "Wrong workflow branch")
    require(git(repo, "branch", "--show-current").decode().strip() == BRANCH, "Wrong checkout")
    require(not git(repo, "status", "--porcelain"), "Dirty checkout; refusing recovery")
    base = git(repo, "rev-parse", "HEAD").decode().strip()
    with tempfile.TemporaryDirectory(prefix="atlas-import-") as temp:
        recovered = Path(temp) / "source.git"
        subprocess.run(["git", "init", "--bare", "--quiet", str(recovered)], check=True)
        git(recovered, "fast-import", "--quiet", input_bytes=stream)
        require(git(recovered, "rev-parse", "refs/heads/main").decode().strip() == SOURCE,
                "Recovered commit mismatch")
        require(git(recovered, "rev-parse", SOURCE + "^{tree}").decode().strip() == TREE,
                "Recovered tree mismatch")
        git(recovered, "fsck", "--full")
        inventory = source_inventory(recovered)
        git(repo, "fetch", "--no-tags", str(recovered), "refs/heads/main")
    ancestor = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", SOURCE, "HEAD"],
                              capture_output=True).returncode
    require(ancestor in (0, 1), "Cannot establish ancestry")
    if ancestor == 0:
        for mode, sha, path in inventory:
            require(git(repo, "ls-files", "--stage", "--", path).decode().startswith(
                    mode + " " + sha + " 0\t"), "Previously imported path changed: " + path)
        return {"status": "already_imported", "source_commit": SOURCE, "source_tree": TREE}
    git(repo, "config", "user.name", "github-actions[bot]")
    git(repo, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    try:
        git(repo, "merge", "--no-ff", "--no-commit", "--allow-unrelated-histories", SOURCE)
        require(not git(repo, "diff", "--cached", "--name-only", "--", ".github/workflows"),
                "Workflows must be pre-seeded identically through the connector")
        for mode, sha, path in inventory:
            require(git(repo, "ls-files", "--stage", "--", path).decode().startswith(
                    mode + " " + sha + " 0\t"), "Restored source differs: " + path)
        subprocess.run([sys.executable, "-m", "compileall", "-q", "src", "scripts"], cwd=repo, check=True)
        subprocess.run([sys.executable, "scripts/validate_context.py"], cwd=repo, check=True)
        receipt = {"schema_version": 1, "kind": "history-preserving-import", "track": "T00",
                   "status": "verified", "source_commit": SOURCE, "source_tree": TREE,
                   "source_files_verified": 252, "bootstrap_parent": base,
                   "compressed_sha256": COMPRESSED, "stream_sha256": STREAM,
                   "python_syntax": "passed", "context_validation": "passed",
                   "bootstrap_python": sys.version.split()[0], "full_test_suite": "not_run_by_importer",
                   "production_runtime_qualified": False, "production_medallion_qualified": False,
                   "hf_writes": 0, "original_payloads_captured": 0,
                   "workflow_run_id": os.environ.get("GITHUB_RUN_ID")}
        path = repo / ".atlas-import/import-receipt.json"
        path.write_text(json.dumps(receipt, indent=2) + "\n")
        git(repo, "add", ".atlas-import/import-receipt.json")
        git(repo, "diff", "--cached", "--check")
        git(repo, "commit", "-m", "chore: restore verified Atlas source and preserve both histories")
        git(repo, "fsck", "--full")
        return receipt
    except Exception:
        subprocess.run(["git", "-C", str(repo), "merge", "--abort"], capture_output=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    repo = Path.cwd()
    stream = verify_transport(repo / ".atlas-import")
    result = restore(repo, stream) if args.restore else {"transport_verified": True, "source_commit": SOURCE}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
