"""Public, immutable source staging with anonymous remote byte verification.

The Hub boundary is injectable for contract tests. Simulated Hub evidence can
never establish that a live dataset exists or that a production layer closed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


import importlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol, TypedDict, Unpack, runtime_checkable

from .crawl import CrawlPolicy, crawl_readiness, validate_state
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file, sha256_json
from .integrity import (
    IDENTIFIER,
    REVISION,
    SHA256,
    atomic_bytes,
    atomic_json,
    read_json,
    safe_path,
    sealed,
    verify_seal,
)
from .parsers import require_interface
from .records import integer, record, records, string

MAX_COMMIT_FILES = 512
LAST_POINTER_RETRY = 2


class ConcurrentUpdateError(RuntimeError):
    """The Hub branch advanced before a conditional commit."""


class HubStore(Protocol):
    """Injectable public staging boundary with immutable revision identifiers."""

    def ensure_public(self) -> None:
        """Create or inspect the target and require public visibility."""
        ...

    def head(self) -> str:
        """Return the current immutable Hub revision.

        Returns:
            The full immutable Hub commit hash.

        """
        ...

    def get(self, path: str, revision: str) -> bytes:
        """Download pinned public bytes anonymously for verification.

        Returns:
            The bytes returned by an anonymous exact-revision download.

        """
        ...

    def put(self, files: dict[str, Path | bytes], *, parent: str | None = None) -> str:
        """Commit bounded files, optionally against an expected parent.

        Returns:
            The immutable commit hash returned for this file transaction.

        Raises:
            HfHubHTTPError: The Hub rejects the transaction for a non-conflict reason.

        """
        ...


class DownloadOptions(TypedDict):
    """Only the SDK download arguments used by immutable public staging."""

    repo_id: str
    repo_type: str
    filename: str
    revision: str
    token: bool
    force_download: bool
    cache_dir: str


@runtime_checkable
class DownloadPort(Protocol):
    """Narrow optional SDK method with an independently validated output path."""

    def hf_hub_download(self, **options: Unpack[DownloadOptions]) -> object:
        """Download exact-revision public bytes to an ephemeral cache.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        ...


class HfStore:
    """Native public staging client with anonymous verification downloads."""

    def __init__(self, repo_id: str, token: str) -> None:
        """Bind the Hub client to the Atlas target and write credential.

        Raises:
            ValueError: The publication target, transaction or immutable revision is
            invalid.

        """
        if not token or repo_id != "edithatogo/au-health-policy-atlas-bronze":
            message = "explicit Atlas Bronze target and write credential required"
            raise ValueError(message)
        from huggingface_hub import HfApi  # ruff: ignore[import-outside-top-level] - Optional backend; core import must remain dependency-free.

        self.repo_id = repo_id
        self.api = HfApi(token=token)

    def ensure_public(self) -> None:
        """Create or inspect the target and require public visibility.

        Raises:
            ValueError: The publication target, transaction or immutable revision is
            invalid.

        """
        self.api.create_repo(
            self.repo_id, repo_type="dataset", exist_ok=True, private=False
        )
        info = self.api.repo_info(self.repo_id, repo_type="dataset")
        if info.private is not False:
            message = "private dataset is not an allowed Atlas publication target"
            raise ValueError(message)
        if not info.sha:
            self.put({
                "README.md": (
                    b"---\nlicense: other\n---\n# Australian Health Policy "
                    b"Atlas Bronze\nStaging only; no corpus completeness "
                    b"or medallion maturity claimed.\n"
                )
            })

    def head(self) -> str:
        """Return the current immutable Hub revision.

        Returns:
            The full immutable Hub commit hash.

        Raises:
            ValueError: The publication target, transaction or immutable revision is
            invalid.

        """
        sha = self.api.repo_info(self.repo_id, repo_type="dataset").sha
        if not isinstance(sha, str) or not REVISION.fullmatch(sha):
            message = "Hub did not return an immutable commit"
            raise ValueError(message)
        return sha

    def get(self, path: str, revision: str) -> bytes:
        """Download pinned public bytes anonymously for verification.

        Returns:
            The bytes returned by an anonymous exact-revision download.

        Raises:
            ValueError: The publication target, transaction or immutable revision is
            invalid.
            FileNotFoundError: The requested input or pinned remote member does not
            exist.

        """
        if not REVISION.fullmatch(revision):
            message = "remote reads require a pinned commit"
            raise ValueError(message)
        downloader = require_interface(
            importlib.import_module("huggingface_hub"), DownloadPort
        )
        from huggingface_hub.errors import EntryNotFoundError  # ruff: ignore[import-outside-top-level] - Optional backend; core import must remain dependency-free.

        try:
            with TemporaryDirectory(prefix="atlas-verify-") as root:
                downloaded = downloader.hf_hub_download(
                    repo_id=self.repo_id,
                    repo_type="dataset",
                    filename=path,
                    revision=revision,
                    token=False,
                    force_download=True,
                    cache_dir=root,
                )
                return Path(string(downloaded)).read_bytes()
        except EntryNotFoundError as exc:
            raise FileNotFoundError(path) from exc

    def put(self, files: dict[str, Path | bytes], *, parent: str | None = None) -> str:
        """Commit bounded files, optionally against an expected parent.

        Returns:
            The immutable commit hash returned for this file transaction.

        Raises:
            ValueError: The publication target, transaction or immutable revision is
            invalid.
            ConcurrentUpdateError: The Hub branch changed before the conditional
            transaction committed.
            HfHubHTTPError: The Hub rejects the transaction for a non-conflict reason.

        """
        from huggingface_hub import CommitOperationAdd  # ruff: ignore[import-outside-top-level] - Optional backend; core import must remain dependency-free.

        if not files or len(files) > MAX_COMMIT_FILES:
            message = "bounded Hub transaction requires 1..512 files"
            raise ValueError(message)
        operations = [
            CommitOperationAdd(
                path_in_repo=name,
                path_or_fileobj=str(data) if isinstance(data, Path) else data,
            )
            for name, data in sorted(files.items())
        ]
        from huggingface_hub.errors import HfHubHTTPError  # ruff: ignore[import-outside-top-level] - Optional backend; core import must remain dependency-free.

        try:
            result = self.api.create_commit(
                repo_id=self.repo_id,
                repo_type="dataset",
                operations=operations,
                parent_commit=parent,
                commit_message="Atlas evidence-bound staging transaction",
            )
        except HfHubHTTPError as exc:
            if exc.response.status_code in {409, 412}:
                message = "conditional Hub commit conflict"
                raise ConcurrentUpdateError(message) from exc
            raise
        if not REVISION.fullmatch(result.oid):
            message = "missing immutable publication commit"
            raise ValueError(message)
        return result.oid


def policy_from_state(state: Mapping[str, object]) -> CrawlPolicy:
    """Validate the persisted crawl policy before using its scope or budgets.

    Returns:
        A validated crawl policy reconstructed from persisted fields.

    """
    return CrawlPolicy.from_record(record(state["policy"]))


def build_stage(workspace: Path, destination: Path) -> dict[str, object]:
    """Assemble a self-hashed staging package from verified crawl state and objects.

    Returns:
        The verified staging manifest written alongside its declared payloads.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    if destination.exists() and any(destination.iterdir()):
        message = "stage destination must be empty"
        raise ValueError(message)
    if destination.resolve().is_relative_to(workspace.resolve()):
        message = "stage must be outside crawl workspace"
        raise ValueError(message)
    state = read_json((workspace / "state.json").read_bytes())
    policy = policy_from_state(state)
    policy.validate()
    validate_state(state, policy, workspace)
    paths = {"state.json"}
    for target in records(state["targets"]):
        if target["status"] == "captured":
            paths.add(string(record(target["receipt"])["object_path"]))
    inventory: list[dict[str, object]] = []
    for name in sorted(paths):
        source = safe_path(workspace, name)
        target = safe_path(destination, name)
        data = source.read_bytes()
        atomic_bytes(target, data)
        inventory.append({
            "path": name,
            "sha256": sha256_bytes(data),
            "size_bytes": len(data),
        })
    manifest = sealed({
        "schema_version": "1.0",
        "kind": "source-staging-package",
        "source_id": policy.source_id,
        "policy_sha256": state["policy_sha256"],
        "state_sha256": state["sha256"],
        "files": inventory,
        "readiness": crawl_readiness(state),
        "not_medallion_release": True,
    })
    atomic_json(destination / "manifest.json", manifest)
    verify_stage(destination)
    return manifest


def verify_stage(root: Path) -> dict[str, object]:
    """Verify the exact staging inventory and its binding to captured source evidence.

    Returns:
        The original manifest after inventory, state and fixity validation.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    manifest = read_json(safe_path(root, "manifest.json").read_bytes())
    verify_seal(manifest)
    if (
        manifest.get("kind") != "source-staging-package"
        or manifest.get("not_medallion_release") is not True
    ):
        message = "not a staging contract"
        raise ValueError(message)
    inventory = records(manifest.get("files", []))
    names = [string(item["path"]) for item in inventory]
    if not names or len(set(names)) != len(names) or "state.json" not in names:
        message = "invalid stage inventory"
        raise ValueError(message)
    _verify_inventory(root, inventory)
    actual = {
        f.relative_to(root).as_posix()
        for f in root.rglob("*")
        if f.is_file() or f.is_symlink()
    }
    if actual != set(names) | {"manifest.json"}:
        message = "untracked stage members"
        raise ValueError(message)
    state = read_json((root / "state.json").read_bytes())
    policy = policy_from_state(state)
    policy.validate()
    validate_state(state, policy, root)
    if (
        state["sha256"] != manifest["state_sha256"]
        or state["policy_sha256"] != manifest["policy_sha256"]
        or policy.source_id != manifest["source_id"]
        or crawl_readiness(state) != manifest["readiness"]
    ):
        message = "stage evidence disagrees with state"
        raise ValueError(message)
    expected = {"state.json"} | {
        string(record(t["receipt"])["object_path"])
        for t in records(state["targets"])
        if t["status"] == "captured"
    }
    if set(names) != expected:
        message = "stage files not bound to captured evidence"
        raise ValueError(message)
    return manifest


def _verify_inventory(root: Path, inventory: list[dict[str, object]]) -> None:
    for item in inventory:
        file = safe_path(root, string(item["path"]))
        if (
            not SHA256.fullmatch(string(item["sha256"]))
            or type(item["size_bytes"]) is not int
            or integer(item["size_bytes"]) < 0
        ):
            message = "invalid object identity"
            raise ValueError(message)
        if (
            file.stat().st_size != item["size_bytes"]
            or sha256_file(file) != item["sha256"]
        ):
            message = "stage object hash or length mismatch"
            raise ValueError(message)


def index_path(policy: CrawlPolicy) -> str:
    """Derive the source index path from the immutable crawl-policy identity.

    Returns:
        The source-specific, policy-hash-bound path within the staging dataset.

    """
    return f"staging/index/{policy.source_id}/{sha256_json(policy.as_dict())}.json"


def restore_stage(
    hub: HubStore, reference: Mapping[str, object], destination: Path
) -> dict[str, object]:
    """Download and rehash a pinned staging package into an empty destination.

    Returns:
        The downloaded manifest after every declared member has been reverified.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    if destination.exists() and any(destination.iterdir()):
        message = "restore destination must be empty"
        raise ValueError(message)
    verify_seal(reference)
    if not REVISION.fullmatch(string(reference["revision"])) or not SHA256.fullmatch(
        string(reference["manifest_sha256"])
    ):
        message = "invalid remote reference"
        raise ValueError(message)
    prefix = f"staging/{reference['source_id']}/{reference['manifest_sha256']}"
    # Validate source_id independently of later crawl-policy checks.
    if not IDENTIFIER.fullmatch(string(reference["source_id"])):
        message = "unsafe source identity"
        raise ValueError(message)
    raw = hub.get(f"{prefix}/manifest.json", string(reference["revision"]))
    manifest = read_json(raw)
    verify_seal(manifest)
    if manifest["sha256"] != reference["manifest_sha256"]:
        message = "remote manifest identity mismatch"
        raise ValueError(message)
    atomic_bytes(destination / "manifest.json", raw)
    for item in records(manifest["files"]):
        path = safe_path(destination, string(item["path"]))
        data = hub.get(f"{prefix}/{item['path']}", string(reference["revision"]))
        if len(data) != item["size_bytes"] or sha256_bytes(data) != item["sha256"]:
            message = "remote byte verification failed"
            raise ValueError(message)
        atomic_bytes(path, data)
    return verify_stage(destination)


def _publish_pointer(
    hub: HubStore,
    index: str,
    previous: dict[str, object] | None,
    reference: dict[str, object],
) -> str:
    """Retry unrelated branch conflicts but never overwrite a changed source index.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.
        RuntimeError: The bounded operation cannot produce a valid terminal result.
        ConcurrentUpdateError: Conditional writes exhaust the bounded retry budget.

    """
    for attempt in range(3):
        parent = hub.head()
        try:
            current = read_json(hub.get(index, parent))
        except FileNotFoundError:
            current = None
        if current != previous:
            message = "source pointer changed; retry from the new remote state"
            raise ValueError(message)
        try:
            return hub.put(
                {index: canonical_json_bytes(reference) + b"\n"}, parent=parent
            )
        except ConcurrentUpdateError:
            if attempt == LAST_POINTER_RETRY:
                raise
    message = "conditional retry budget unexpectedly exhausted"
    raise RuntimeError(message)


def publish_stage(hub: HubStore, stage: Path) -> dict[str, object]:
    """Publish, anonymously verify and conditionally index staging bytes.

    Returns:
        The immutable publication revision and remote verification observation.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
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
        if integer(previous["generation"]) > integer(state["generation"]):
            message = "refusing stale checkpoint rollback"
            raise ValueError(message)
        if (
            previous["generation"] == state["generation"]
            and previous["manifest_sha256"] != manifest["sha256"]
        ):
            message = "conflicting checkpoint generation"
            raise ValueError(message)
    prefix = f"staging/{policy.source_id}/{manifest['sha256']}"
    files: dict[str, Path | bytes] = {
        f"{prefix}/{item['path']}": safe_path(stage, string(item["path"]))
        for item in records(manifest["files"])
    }
    files[f"{prefix}/manifest.json"] = stage / "manifest.json"
    revision = hub.put(files)
    reference = sealed({
        "schema_version": "1.0",
        "kind": "verified-source-reference",
        "source_id": policy.source_id,
        "manifest_sha256": manifest["sha256"],
        "policy_sha256": manifest["policy_sha256"],
        "generation": state["generation"],
        "revision": revision,
        "not_medallion_release": True,
    })
    with TemporaryDirectory(prefix="atlas-clean-verify-") as temporary:
        restore_stage(hub, reference, Path(temporary))
    pointer_commit = _publish_pointer(hub, index, previous, reference)
    if hub.get(index, pointer_commit) != canonical_json_bytes(reference) + b"\n":
        message = "remote pointer byte verification failed"
        raise ValueError(message)
    return sealed({
        "kind": "publication-observation",
        "reference": reference,
        "pointer_commit": pointer_commit,
        "remote_bytes_verified": True,
        "gate_b_passed": False,
    })


def restore_source(
    hub: HubStore, policy: CrawlPolicy, destination: Path, *, revision: str
) -> dict[str, object]:
    """Restore a verified source checkpoint, rejecting missing payloads.

    Returns:
        The verified manifest for the checkpoint restored into the crawl workspace.

    Raises:
        ValueError: Source scope, identity or resource-budget validation fails.

    """
    reference = read_json(hub.get(index_path(policy), revision))
    try:
        manifest = restore_stage(hub, reference, destination)
    except FileNotFoundError as exc:
        message = "referenced remote checkpoint object missing"
        raise ValueError(message) from exc
    if manifest["source_id"] != policy.source_id or manifest[
        "policy_sha256"
    ] != sha256_json(policy.as_dict()):
        message = "restored source has the wrong scope"
        raise ValueError(message)
    # The stage manifest is a transport member, not mutable crawl state.
    (destination / "manifest.json").unlink()
    return manifest


def _assess_source(
    hub: HubStore, policy: CrawlPolicy, revision: str
) -> tuple[dict[str, object], bool]:
    with TemporaryDirectory(prefix="atlas-bronze-verify-") as temporary:
        root = Path(temporary)
        manifest = restore_source(hub, policy, root, revision=revision)
        state = read_json((root / "state.json").read_bytes())
        reference = read_json(hub.get(index_path(policy), revision))
        source = {
            "source_id": policy.source_id,
            "reference": reference,
            "readiness": manifest["readiness"],
            "boundaries": state["boundaries"],
        }
        return source, crawl_readiness(state)["scope_complete"] is True


def qualify_remote_bronze(
    hub: HubStore,
    policies: list[CrawlPolicy],
    *,
    census_sha256: str,
    code_revision: str,
) -> dict[str, object]:
    """Assess each declared source independently while retaining the closed Bronze gate.

    Returns:
        Per-source findings and blockers, with production Gate B still false.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    if not policies or len({p.source_id for p in policies}) != len(policies):
        message = "nonempty unique source scope required"
        raise ValueError(message)
    if not SHA256.fullmatch(census_sha256) or not REVISION.fullmatch(code_revision):
        message = "exact census and code identities required"
        raise ValueError(message)
    head = hub.head()
    sources: list[dict[str, object]] = []
    blocked: list[dict[str, object]] = []
    for policy in policies:
        policy.validate()
        try:
            source, complete = _assess_source(hub, policy, head)
            if not complete:
                blocked.append({
                    "source_id": policy.source_id,
                    "reason": "source_scope_incomplete",
                })
            sources.append(source)
        except (FileNotFoundError, TypeError, ValueError) as exc:
            blocked.append({"source_id": policy.source_id, "reason": str(exc)})
    return sealed({
        "schema_version": "1.0",
        "kind": "bronze-remote-assessment",
        "release_id": "bronze-v1",
        "census_sha256": census_sha256,
        "code_revision": code_revision,
        "assessment_revision": head,
        "expected_sources": len(policies),
        "sources": sources,
        "blocked": blocked,
        "data_candidate_ready": len(sources) == len(policies) and not blocked,
        "gate_b_passed": False,
        "scope_note": "Declared bounded source scope only, not a statewide census.",
    })
