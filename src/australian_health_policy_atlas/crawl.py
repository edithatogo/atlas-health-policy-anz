"""Finite, resumable acquisition of explicitly bounded official source surfaces.

Exhausting a declared HTML frontier is not proof of statewide corpus coverage.
This module cannot mark Bronze published or enable downstream medallion work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urlsplit

from .capture import CapturePort, CaptureReceipt, capture_url
from .discovery import discover_links
from .hashing import sha256_file, sha256_json
from .integrity import (
    IDENTIFIER,
    atomic_json,
    read_json,
    safe_path,
    sealed,
    verify_seal,
)
from .records import integer, record, records, string, strings
from .source_registry import JURISDICTIONS

SERVER_ERROR_START = 500
FIRST_VISIBLE_ASCII = 33


@dataclass(frozen=True)
class CrawlPolicy:
    """Immutable source scope and finite resource budgets."""

    source_id: str
    jurisdiction: str
    seed_url: str
    allowed_hosts: tuple[str, ...]
    cutoff: str
    max_depth: int = 2
    max_targets: int = 250
    max_links_per_page: int = 100
    max_attempts: int = 3
    max_bytes: int = 32 * 1024 * 1024
    policy_version: str = "bounded-html-v1"

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> CrawlPolicy:
        """Validate serialized policy fields rather than unpacking untyped JSON.

        Returns:
            The result described above, retaining the declared return-type contract.

        """
        result = cls(
            source_id=string(value["source_id"]),
            jurisdiction=string(value["jurisdiction"]),
            seed_url=string(value["seed_url"]),
            allowed_hosts=tuple(strings(value["allowed_hosts"])),
            cutoff=string(value["cutoff"]),
            max_depth=integer(value.get("max_depth", 2)),
            max_targets=integer(value.get("max_targets", 250)),
            max_links_per_page=integer(value.get("max_links_per_page", 100)),
            max_attempts=integer(value.get("max_attempts", 3)),
            max_bytes=integer(value.get("max_bytes", 32 * 1024 * 1024)),
            policy_version=string(value.get("policy_version", "bounded-html-v1")),
        )
        result.validate()
        return result

    def as_dict(self) -> dict[str, object]:
        """Serialize explicit fields without discarding their type contracts.

        Returns:
            A dictionary containing this record's declared fields.

        """
        return {
            "source_id": self.source_id,
            "jurisdiction": self.jurisdiction,
            "seed_url": self.seed_url,
            "allowed_hosts": self.allowed_hosts,
            "cutoff": self.cutoff,
            "max_depth": self.max_depth,
            "max_targets": self.max_targets,
            "max_links_per_page": self.max_links_per_page,
            "max_attempts": self.max_attempts,
            "max_bytes": self.max_bytes,
            "policy_version": self.policy_version,
        }

    def validate(self) -> None:
        """Reject invalid source identities, host boundaries and capture budgets.

        Raises:
            ValueError: The supplied data violates the function's documented
            validation contract.

        """
        if not IDENTIFIER.fullmatch(self.source_id):
            message = "invalid source identity"
            raise ValueError(message)
        if self.jurisdiction not in JURISDICTIONS:
            message = "invalid jurisdiction"
            raise ValueError(message)
        if (
            not self.cutoff
            or not self.allowed_hosts
            or any(h != h.lower() or not h or "/" in h for h in self.allowed_hosts)
        ):
            message = "explicit cutoff and lowercase allowed hosts required"
            raise ValueError(message)
        for n in (
            self.max_targets,
            self.max_links_per_page,
            self.max_attempts,
            self.max_bytes,
        ):
            if type(n) is not int or n <= 0:
                message = "budgets must be positive integers"
                raise ValueError(message)
        if type(self.max_depth) is not int or self.max_depth < 0:
            message = "invalid max_depth"
            raise ValueError(message)
        check_url(self.seed_url, self.allowed_hosts)


def check_url(url: str, hosts: tuple[str, ...]) -> None:
    """Enforce the configured HTTPS host, port and location boundaries.

    Raises:
        ValueError: Source scope, identity or resource-budget validation fails.

    """
    parts = urlsplit(url)
    invalid_authority = parts.hostname not in hosts or parts.username or parts.password
    invalid_location = parts.fragment or any(ord(c) < FIRST_VISIBLE_ASCII for c in url)
    if (
        parts.scheme != "https"
        or invalid_authority
        or parts.port not in {None, 443}
        or invalid_location
    ):
        message = "URL outside explicit HTTPS source boundary"
        raise ValueError(message)


def _new_target(url: str, depth: int, parent: str | None) -> dict[str, object]:
    return {
        "url": url,
        "depth": depth,
        "parent": parent,
        "status": "queued",
        "attempts": 0,
    }


def _fresh(policy: CrawlPolicy) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "kind": "source-crawl-state",
        "policy": policy.as_dict(),
        "policy_sha256": sha256_json(policy.as_dict()),
        "targets": [_new_target(policy.seed_url, 0, None)],
        "boundaries": [],
        "generation": 0,
    }


def _validate_lineage(
    target: Mapping[str, object],
    targets: list[dict[str, object]],
    policy: CrawlPolicy,
) -> None:
    depth = integer(target["depth"])
    attempts = integer(target["attempts"])
    if not 0 <= depth <= policy.max_depth or not 0 <= attempts <= policy.max_attempts:
        message = "invalid target budget state"
        raise ValueError(message)
    if depth == 0:
        if target["url"] != policy.seed_url or target["parent"] is not None:
            message = "invalid root target"
            raise ValueError(message)
    else:
        parents = [item for item in targets if item["url"] == target["parent"]]
        if len(parents) != 1 or integer(parents[0]["depth"]) + 1 != depth:
            message = "invalid parent/depth lineage"
            raise ValueError(message)


def _validate_receipt(
    target: Mapping[str, object], policy: CrawlPolicy, root: Path
) -> None:
    receipt = record(target["receipt"])
    if receipt["requested_url"] != target["url"]:
        message = "receipt target mismatch"
        raise ValueError(message)
    check_url(string(receipt["final_url"]), policy.allowed_hosts)
    obj = safe_path(root, string(receipt["object_path"]))
    if (
        obj.stat().st_size != receipt["size_bytes"]
        or sha256_file(obj) != receipt["sha256"]
    ):
        message = "captured object fixity mismatch"
        raise ValueError(message)


DISPOSITIONS = (
    "queued",
    "retryable",
    "captured",
    "unavailable",
    "restricted",
    "oversized",
    "failed",
)


def validate_state(
    state: Mapping[str, object], policy: CrawlPolicy, root: Path
) -> None:
    """Verify state identity, lineage, budgets and captured-byte fixity.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    verify_seal(state)
    if state.get("kind") != "source-crawl-state" or state.get(
        "policy_sha256"
    ) != sha256_json(policy.as_dict()):
        message = "crawl policy changed; start a new release scope"
        raise ValueError(message)
    if sha256_json(state.get("policy")) != state["policy_sha256"]:
        message = "policy identity mismatch"
        raise ValueError(message)
    targets = records(state.get("targets", []))
    if not targets or len(targets) > policy.max_targets:
        message = "invalid target cardinality"
        raise ValueError(message)
    seen: set[str] = set()
    for target in targets:
        url = string(target["url"])
        check_url(url, policy.allowed_hosts)
        if url in seen:
            message = "duplicate target"
            raise ValueError(message)
        _validate_lineage(target, targets, policy)
        seen.add(url)
        if target["status"] not in DISPOSITIONS:
            message = "unknown target disposition"
            raise ValueError(message)
        if target["status"] == "captured":
            _validate_receipt(target, policy, root)


def crawl_readiness(state: Mapping[str, object]) -> dict[str, object]:
    """Summarise the declared crawl frontier without inferring statewide completeness.

    Returns:
        Counts, boundaries and readiness of the configured crawl scope only.

    """
    counts = {
        key: sum(t["status"] == key for t in records(state["targets"]))
        for key in (
            "queued",
            "retryable",
            "captured",
            "unavailable",
            "restricted",
            "oversized",
            "failed",
        )
    }
    exhausted = counts["queued"] + counts["retryable"] == 0
    return {
        "counts": counts,
        "frontier_exhausted": exhausted,
        "scope_complete": exhausted
        and not state["boundaries"]
        and counts["captured"] > 0
        and not any(counts[k] for k in ("restricted", "oversized", "failed")),
        "state_sha256": state["sha256"],
        "state_generation": state["generation"],
        "not_corpus_completeness": True,
        "gate_b_passed": False,
    }


def _store_capture(
    receipt: CaptureReceipt,
    target: dict[str, object],
    policy: CrawlPolicy,
    root: Path,
) -> Path:
    if receipt.requested_url != target["url"]:
        message = "capture returned a different target"
        raise ValueError(message)
    check_url(receipt.final_url, policy.allowed_hosts)
    path = Path(receipt.stored_path)
    if not path.resolve().is_relative_to(root.resolve()):
        message = "capture escaped workspace"
        raise ValueError(message)
    if path.stat().st_size != receipt.size_bytes or sha256_file(path) != receipt.sha256:
        message = "capture fixity mismatch"
        raise ValueError(message)
    row = receipt.as_dict()
    row.pop("stored_path")
    row["object_path"] = path.relative_to(root).as_posix()
    target.update(status="captured", receipt=row)
    target.pop("error", None)
    return path


def _boundary_reason(
    url: str,
    policy: CrawlPolicy,
    depth: int,
    offset: int,
    target_count: int,
) -> str | None:
    try:
        check_url(url, policy.allowed_hosts)
    except ValueError:
        return "external_or_disallowed_candidate"
    if depth >= policy.max_depth:
        return "depth_limit"
    if offset >= policy.max_links_per_page:
        return "link_limit"
    if target_count >= policy.max_targets:
        return "target_limit"
    return None


def _discover_children(
    path: Path,
    receipt: CaptureReceipt,
    target: dict[str, object],
    policy: CrawlPolicy,
    state: dict[str, object],
) -> None:
    if receipt.media_type not in {"text/html", "application/xhtml+xml"}:
        return
    html = path.read_bytes().decode("utf-8", errors="replace")
    targets = records(state["targets"])
    boundaries = records(state["boundaries"])
    state["targets"], state["boundaries"] = targets, boundaries
    known = {string(item["url"]) for item in targets}
    links = discover_links(html, base_url=receipt.final_url, same_host_only=False)
    candidates = [
        link
        for link in links
        if link.likely_document
        or "page=" in link.url
        or "next" in link.anchor_text.lower()
    ]
    for offset, link in enumerate(candidates):
        url = urldefrag(link.url)[0]
        if url in known:
            continue
        reason = _boundary_reason(
            url, policy, integer(target["depth"]), offset, len(targets)
        )
        if reason:
            boundary = {"parent": target["url"], "url": url, "reason": reason}
            if boundary not in boundaries:
                boundaries.append(boundary)
        else:
            targets.append(
                _new_target(url, integer(target["depth"]) + 1, string(target["url"]))
            )
            known.add(url)


def _http_status(code: int, retry: str) -> str:
    if code in {404, 410}:
        return "unavailable"
    if code in {401, 403}:
        return "restricted"
    if code in {408, 425, 429} or code >= SERVER_ERROR_START:
        return retry
    return "failed"


def _capture_target(
    target: dict[str, object],
    policy: CrawlPolicy,
    root: Path,
    state: dict[str, object],
    fetch: CapturePort,
) -> None:
    attempts = integer(target["attempts"]) + 1
    target["attempts"] = attempts
    retry = "retryable" if attempts < policy.max_attempts else "failed"
    try:
        receipt = fetch(
            string(target["url"]),
            cas_root=root / "cas",
            max_bytes=policy.max_bytes,
            retries=0,
            allowed_hosts=policy.allowed_hosts,
        )
        path = _store_capture(receipt, target, policy, root)
        _discover_children(path, receipt, target, policy, state)
    except HTTPError as exc:
        exc.close()
        target["status"] = _http_status(exc.code, retry)
        target["error"] = {"type": "HTTPError", "status": exc.code}
    except (URLError, TimeoutError, OSError) as exc:
        target["status"] = retry
        target["error"] = {"type": type(exc).__name__}
    except (TypeError, ValueError) as exc:
        target["status"] = "oversized" if "max_bytes" in str(exc) else "failed"
        target["error"] = {"type": type(exc).__name__, "reason": str(exc)}


def run_crawl(
    policy: CrawlPolicy,
    root: Path,
    *,
    request_budget: int = 20,
    fetch: CapturePort = capture_url,
) -> dict[str, object]:
    """Advance a finite crawl and persist each capture or explicit failure.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    policy.validate()
    if type(request_budget) is not int or request_budget <= 0:
        message = "positive invocation request budget required"
        raise ValueError(message)
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "state.json"
    state = (
        read_json(state_path.read_bytes())
        if state_path.exists()
        else sealed(_fresh(policy))
    )
    validate_state(state, policy, root)
    requests = 0
    index = 0
    while index < len(records(state["targets"])) and requests < request_budget:
        target = records(state["targets"])[index]
        index += 1
        if target["status"] not in {"queued", "retryable"}:
            continue
        requests += 1
        _capture_target(target, policy, root, state, fetch)
        state["generation"] = integer(state["generation"]) + 1
        state = sealed(state)
        atomic_json(state_path, state)
    atomic_json(state_path, state)
    validate_state(state, policy, root)
    return sealed({
        "schema_version": "1.0",
        "kind": "crawl-readiness",
        **crawl_readiness(state),
    })
