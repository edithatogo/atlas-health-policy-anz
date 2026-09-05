"""Public, immutable source staging with anonymous remote byte verification.

The Hub boundary is injectable for contract tests. Simulated Hub evidence can
never establish that a live dataset exists or that a production layer closed.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Protocol

from .crawl import CrawlPolicy, crawl_readiness, validate_state
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .integrity import REVISION, SHA256, atomic_bytes, atomic_json, read_json, safe_path, sealed, verify_seal


class ConcurrentUpdateError(RuntimeError):
    """The Hub branch advanced before a conditional commit."""


class HubStore(Protocol):
    def ensure_public(self) -> None: ...
    def head(self) -> str: ...
    def get(self, path: str, revision: str) -> bytes: ...
    def put(self, files: dict[str, Path | bytes], *, parent: str | None = None) -> str: ...


class HfStore:
    """Native Hub client. Writes use credentials; verification downloads are anonymous."""
    def __init__(self, repo_id: str, token: str) -> None:
        if not token or repo_id != "edithatogo/au-health-policy-atlas-bronze":
            raise ValueError("explicit Atlas Bronze target and write credential required")
        from huggingface_hub import HfApi
        self.repo_id = repo_id
        self.api = HfApi(token=token)

    def ensure_public(self) -> None:
        self.api.create_repo(self.repo_id, repo_type="dataset", exist_ok=True, private=False)
        info = self.api.repo_info(self.repo_id, repo_type="dataset")
        if info.private is not False:
            raise ValueError("private dataset is not an allowed Atlas publication target")
        if not info.sha:
            self.put({"README.md": b"---\nlicense: other\n---\n# Australian Health Policy Atlas Bronze\nStaging only; no corpus completeness or medallion maturity claimed.\n"})

    def head(self) -> str:
        sha = self.api.repo_info(self.repo_id, repo_type="dataset").sha
        if not REVISION.fullmatch(sha):
            raise ValueError("Hub did not return an immutable commit")
        return sha

    def get(self, path: str, revision: str) -> bytes:
        if not REVISION.fullmatch(revision):
            raise ValueError("remote reads require a pinned commit")
        from huggingface_hub import hf_hub_download
        from huggingface_hub.errors import EntryNotFoundError
        try:
            with TemporaryDirectory(prefix="atlas-verify-") as root:
                downloaded = hf_hub_download(repo_id=self.repo_id, repo_type="dataset",
                    filename=path, revision=revision, token=False, force_download=True,
                    cache_dir=root)
                return Path(downloaded).read_bytes()
        except EntryNotFoundError as exc:
            raise FileNotFoundError(path) from exc

    def put(self, files: dict[str, Path | bytes], *, parent: str | None = None) -> str:
        from huggingface_hub import CommitOperationAdd
        if not files or len(files) > 512:
            raise ValueError("bounded Hub transaction requires 1..512 files")
        operations = [CommitOperationAdd(path_in_repo=name,
            path_or_fileobj=str(data) if isinstance(data, Path) else data)
            for name, data in sorted(files.items())]
        from huggingface_hub.errors import HfHubHTTPError
        try:
            result = self.api.create_commit(repo_id=self.repo_id, repo_type="dataset",
                operations=operations, parent_commit=parent,
                commit_message="Atlas evidence-bound staging transaction")
        except HfHubHTTPError as exc:
            if exc.response is not None and exc.response.status_code in {409, 412}:
                raise ConcurrentUpdateError("conditional Hub commit conflict") from exc
            raise
        if not REVISION.fullmatch(result.oid):
            raise ValueError("missing immutable publication commit")
        return result.oid


def policy_from_state(state: dict[str, Any]) -> CrawlPolicy:
    fields = dict(state["policy"])
    fields["allowed_hosts"] = tuple(fields["allowed_hosts"])
    return CrawlPolicy(**fields)


def build_stage(workspace: Path, destination: Path) -> dict[str, Any]:
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("stage destination must be empty")
    if destination.resolve().is_relative_to(workspace.resolve()):
        raise ValueError("stage must be outside crawl workspace")
    state = read_json((workspace / "state.json").read_bytes())
    policy = policy_from_state(state)
    policy.validate()
    validate_state(state, policy, workspace)
    paths = {"state.json"}
    for target in state["targets"]:
        if target["status"] == "captured":
            paths.add(target["receipt"]["object_path"])
    inventory = []
    for name in sorted(paths):
        source = safe_path(workspace, name)
        target = safe_path(destination, name)
        data = source.read_bytes()
        atomic_bytes(target, data)
        inventory.append({"path": name, "sha256": sha256_bytes(data), "size_bytes": len(data)})
    manifest = sealed({"schema_version": "1.0", "kind": "source-staging-package",
        "source_id": policy.source_id, "policy_sha256": state["policy_sha256"],
        "state_sha256": state["sha256"], "files": inventory,
        "readiness": crawl_readiness(state), "not_medallion_release": True})
    atomic_json(destination / "manifest.json", manifest)
    verify_stage(destination)
    return manifest


def verify_stage(root: Path) -> dict[str, Any]:
    manifest = read_json(safe_path(root, "manifest.json").read_bytes())
    verify_seal(manifest)
    if manifest.get("kind") != "source-staging-package" or manifest.get("not_medallion_release") is not True:
        raise ValueError("not a staging contract")
    inventory = manifest.get("files", [])
    names = [item["path"] for item in inventory]
    if not names or len(set(names)) != len(names) or "state.json" not in names:
        raise ValueError("invalid stage inventory")
    for item in inventory:
        file = safe_path(root, item["path"])
        if not SHA256.fullmatch(item["sha256"]) or type(item["size_bytes"]) is not int or item["size_bytes"] < 0:
            raise ValueError("invalid object identity")
        if file.stat().st_size != item["size_bytes"] or sha256_file(file) != item["sha256"]:
            raise ValueError("stage object hash or length mismatch")
    actual = {f.relative_to(root).as_posix() for f in root.rglob("*") if f.is_file() or f.is_symlink()}
    if actual != set(names) | {"manifest.json"}:
        raise ValueError("untracked stage members")
    state = read_json((root / "state.json").read_bytes())
    policy = policy_from_state(state)
    policy.validate()
    validate_state(state, policy, root)
    if (state["sha256"] != manifest["state_sha256"] or state["policy_sha256"] != manifest["policy_sha256"] or
            policy.source_id != manifest["source_id"] or crawl_readiness(state) != manifest["readiness"]):
        raise ValueError("stage evidence disagrees with state")
    expected = {"state.json"} | {t["receipt"]["object_path"] for t in state["targets"] if t["status"] == "captured"}
    if set(names) != expected:
        raise ValueError("stage files not bound to captured evidence")
    return manifest


def index_path(policy: CrawlPolicy) -> str:
    from dataclasses import asdict
    from .hashing import sha256_json
    return f"staging/index/{policy.source_id}/{sha256_json(asdict(policy))}.json"


def _remote_stage(hub: HubStore, reference: dict[str, Any], destination: Path) -> dict[str, Any]:
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("restore destination must be empty")
    verify_seal(reference)
    if not REVISION.fullmatch(reference["revision"]) or not SHA256.fullmatch(reference["manifest_sha256"]):
        raise ValueError("invalid remote reference")
    prefix = f"staging/{reference['source_id']}/{reference['manifest_sha256']}"
    # Reject path injection in source_id through normal source policy validation below too.
    from .integrity import IDENTIFIER
    if not IDENTIFIER.fullmatch(reference["source_id"]):
        raise ValueError("unsafe source identity")
    raw = hub.get(f"{prefix}/manifest.json", reference["revision"])
    manifest = read_json(raw)
    verify_seal(manifest)
    if manifest["sha256"] != reference["manifest_sha256"]:
        raise ValueError("remote manifest identity mismatch")
    atomic_bytes(destination / "manifest.json", raw)
    for item in manifest["files"]:
        path = safe_path(destination, item["path"])
        data = hub.get(f"{prefix}/{item['path']}", reference["revision"])
        if len(data) != item["size_bytes"] or sha256_bytes(data) != item["sha256"]:
            raise ValueError("remote byte verification failed")
        atomic_bytes(path, data)
    return verify_stage(destination)


def publish_stage(hub: HubStore, stage: Path) -> dict[str, Any]:
    manifest = verify_stage(stage)
    state = read_json((stage / "state.json").read_bytes())
    policy = policy_from_state(state)
    hub.ensure_public()
    index = index_path(policy)
    head = hub.head()
    try:
        previous = read_json(hub.get(index, head))
    except FileNotFoundError:
        previous = None
    if previous is not None:
        verify_seal(previous)
        if previous["generation"] > state["generation"]:
            raise ValueError("refusing stale checkpoint rollback")
        if previous["generation"] == state["generation"] and previous["manifest_sha256"] != manifest["sha256"]:
            raise ValueError("conflicting checkpoint generation")
    prefix = f"staging/{policy.source_id}/{manifest['sha256']}"
    files = {f"{prefix}/{item['path']}": safe_path(stage, item["path"]) for item in manifest["files"]}
    files[f"{prefix}/manifest.json"] = stage / "manifest.json"
    revision = hub.put(files)
    reference = sealed({"schema_version": "1.0", "kind": "verified-source-reference",
        "source_id": policy.source_id, "manifest_sha256": manifest["sha256"],
        "policy_sha256": manifest["policy_sha256"], "generation": state["generation"],
        "revision": revision, "not_medallion_release": True})
    with TemporaryDirectory(prefix="atlas-clean-verify-") as temporary:
        _remote_stage(hub, reference, Path(temporary))
    # Cross-source commits can advance the same dataset branch. Retry only
    # conditional conflicts, never overwrite a concurrently changed source index.
    for attempt in range(3):
        parent = hub.head()
        try:
            current = read_json(hub.get(index, parent))
        except FileNotFoundError:
            current = None
        if current != previous:
            raise ValueError("source pointer changed; retry from the new remote state")
        try:
            pointer_commit = hub.put({index: canonical_json_bytes(reference) + b"\n"}, parent=parent)
            break
        except ConcurrentUpdateError:
            if attempt == 2:
                raise
    if hub.get(index, pointer_commit) != canonical_json_bytes(reference) + b"\n":
        raise ValueError("remote pointer byte verification failed")
    return sealed({"kind": "publication-observation", "reference": reference,
        "pointer_commit": pointer_commit, "remote_bytes_verified": True,
        "gate_b_passed": False})


def restore_source(hub: HubStore, policy: CrawlPolicy, destination: Path, *, revision: str) -> dict[str, Any]:
    reference = read_json(hub.get(index_path(policy), revision))
    try:
        manifest = _remote_stage(hub, reference, destination)
    except FileNotFoundError as exc:
        raise ValueError("referenced remote checkpoint object missing") from exc
    from dataclasses import asdict
    from .hashing import sha256_json
    if manifest["source_id"] != policy.source_id or manifest["policy_sha256"] != sha256_json(asdict(policy)):
        raise ValueError("restored source has the wrong scope")
    # The stage manifest is a transport member, not mutable crawl state.
    (destination / "manifest.json").unlink()
    return manifest


def qualify_remote_bronze(hub: HubStore, policies: list[CrawlPolicy], *, census_sha256: str,
                          code_revision: str) -> dict[str, Any]:
    if not policies or len({p.source_id for p in policies}) != len(policies):
        raise ValueError("nonempty unique source scope required")
    if not SHA256.fullmatch(census_sha256) or not REVISION.fullmatch(code_revision):
        raise ValueError("exact census and code identities required")
    head = hub.head()
    sources, blocked = [], []
    for policy in policies:
        policy.validate()
        try:
            with TemporaryDirectory(prefix="atlas-bronze-verify-") as temporary:
                root = Path(temporary)
                manifest = restore_source(hub, policy, root, revision=head)
                state = read_json((root / "state.json").read_bytes())
                reference = read_json(hub.get(index_path(policy), head))
                if not crawl_readiness(state)["scope_complete"]:
                    blocked.append({"source_id": policy.source_id, "reason": "source_scope_incomplete"})
                sources.append({"source_id": policy.source_id, "reference": reference,
                    "readiness": manifest["readiness"], "boundaries": state["boundaries"]})
        except (FileNotFoundError, ValueError) as exc:
            blocked.append({"source_id": policy.source_id, "reason": str(exc)})
    return sealed({"schema_version": "1.0", "kind": "bronze-remote-assessment",
        "release_id": "bronze-v1", "census_sha256": census_sha256,
        "code_revision": code_revision, "assessment_revision": head,
        "expected_sources": len(policies), "sources": sources, "blocked": blocked,
        "data_candidate_ready": len(sources) == len(policies) and not blocked,
        "gate_b_passed": False, "scope_note": "Declared bounded source scope only, not a statewide census."})
