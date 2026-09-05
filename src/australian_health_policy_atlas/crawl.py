"""Finite, resumable acquisition of explicitly bounded official source surfaces.

Exhausting a declared HTML frontier is not proof of statewide corpus coverage.
This module cannot mark Bronze published or enable downstream medallion work.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urlsplit

from .capture import CaptureReceipt, capture_url
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
from .source_registry import JURISDICTIONS


@dataclass(frozen=True)
class CrawlPolicy:
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

    def validate(self) -> None:
        if not IDENTIFIER.fullmatch(self.source_id):
            raise ValueError("invalid source identity")
        if self.jurisdiction not in JURISDICTIONS:
            raise ValueError("invalid jurisdiction")
        if (
            not self.cutoff
            or not self.allowed_hosts
            or any(h != h.lower() or not h or "/" in h for h in self.allowed_hosts)
        ):
            raise ValueError("explicit cutoff and lowercase allowed hosts required")
        for n in (
            self.max_targets,
            self.max_links_per_page,
            self.max_attempts,
            self.max_bytes,
        ):
            if type(n) is not int or n <= 0:
                raise ValueError("budgets must be positive integers")
        if type(self.max_depth) is not int or self.max_depth < 0:
            raise ValueError("invalid max_depth")
        check_url(self.seed_url, self.allowed_hosts)


def check_url(url: str, hosts: tuple[str, ...]) -> None:
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname not in hosts
        or parts.username
        or parts.password
        or parts.port not in (None, 443)
        or parts.fragment
        or any(ord(c) < 33 for c in url)
    ):
        raise ValueError("URL outside explicit HTTPS source boundary")


def _new_target(url: str, depth: int, parent: str | None) -> dict[str, Any]:
    return {
        "url": url,
        "depth": depth,
        "parent": parent,
        "status": "queued",
        "attempts": 0,
    }


def _fresh(policy: CrawlPolicy) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "kind": "source-crawl-state",
        "policy": asdict(policy),
        "policy_sha256": sha256_json(asdict(policy)),
        "targets": [_new_target(policy.seed_url, 0, None)],
        "boundaries": [],
        "generation": 0,
    }


def validate_state(state: dict[str, Any], policy: CrawlPolicy, root: Path) -> None:
    verify_seal(state)
    if state.get("kind") != "source-crawl-state" or state.get(
        "policy_sha256"
    ) != sha256_json(asdict(policy)):
        raise ValueError("crawl policy changed; start a new release scope")
    if sha256_json(state.get("policy")) != state["policy_sha256"]:
        raise ValueError("policy identity mismatch")
    targets = state.get("targets", [])
    if not targets or len(targets) > policy.max_targets:
        raise ValueError("invalid target cardinality")
    seen: set[str] = set()
    for target in targets:
        url = target["url"]
        check_url(url, policy.allowed_hosts)
        if url in seen:
            raise ValueError("duplicate target")
        if (
            type(target["depth"]) is not int
            or not 0 <= target["depth"] <= policy.max_depth
            or type(target["attempts"]) is not int
            or not 0 <= target["attempts"] <= policy.max_attempts
        ):
            raise ValueError("invalid target budget state")
        if target["depth"] == 0:
            if url != policy.seed_url or target["parent"] is not None:
                raise ValueError("invalid root target")
        else:
            parents = [t for t in targets if t["url"] == target["parent"]]
            if len(parents) != 1 or parents[0]["depth"] + 1 != target["depth"]:
                raise ValueError("invalid parent/depth lineage")
        seen.add(url)
        if target["status"] not in {
            "queued",
            "retryable",
            "captured",
            "unavailable",
            "restricted",
            "oversized",
            "failed",
        }:
            raise ValueError("unknown target disposition")
        if target["status"] == "captured":
            receipt = target["receipt"]
            if receipt["requested_url"] != url:
                raise ValueError("receipt target mismatch")
            check_url(receipt["final_url"], policy.allowed_hosts)
            obj = safe_path(root, receipt["object_path"])
            if (
                obj.stat().st_size != receipt["size_bytes"]
                or sha256_file(obj) != receipt["sha256"]
            ):
                raise ValueError("captured object fixity mismatch")


def crawl_readiness(state: dict[str, Any]) -> dict[str, Any]:
    counts = {
        key: sum(t["status"] == key for t in state["targets"])
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


def run_crawl(
    policy: CrawlPolicy,
    root: Path,
    *,
    request_budget: int = 20,
    fetch: Callable[..., CaptureReceipt] = capture_url,
) -> dict[str, Any]:
    policy.validate()
    if type(request_budget) is not int or request_budget <= 0:
        raise ValueError("positive invocation request budget required")
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
    while index < len(state["targets"]) and requests < request_budget:
        target = state["targets"][index]
        index += 1
        if target["status"] not in {"queued", "retryable"}:
            continue
        requests += 1
        target["attempts"] += 1
        try:
            receipt = fetch(
                target["url"],
                cas_root=root / "cas",
                max_bytes=policy.max_bytes,
                retries=0,
                allowed_hosts=policy.allowed_hosts,
            )
            if receipt.requested_url != target["url"]:
                raise ValueError("capture returned a different target")
            check_url(receipt.final_url, policy.allowed_hosts)
            path = Path(receipt.stored_path)
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("capture escaped workspace")
            if (
                path.stat().st_size != receipt.size_bytes
                or sha256_file(path) != receipt.sha256
            ):
                raise ValueError("capture fixity mismatch")
            row = receipt.as_dict()
            row.pop("stored_path")
            row["object_path"] = path.relative_to(root).as_posix()
            target.update(status="captured", receipt=row)
            target.pop("error", None)
            if receipt.media_type in {"text/html", "application/xhtml+xml"}:
                html = path.read_bytes().decode("utf-8", errors="replace")
                known = {t["url"] for t in state["targets"]}
                links = discover_links(
                    html, base_url=receipt.final_url, same_host_only=False
                )
                candidates = [
                    l
                    for l in links
                    if l.likely_document
                    or "page=" in l.url
                    or "next" in l.anchor_text.lower()
                ]
                # Persist explicit exclusions and budget boundaries instead of silently truncating.
                for offset, link in enumerate(candidates):
                    url = urldefrag(link.url)[0]
                    if url in known:
                        continue
                    reason = None
                    try:
                        check_url(url, policy.allowed_hosts)
                    except ValueError:
                        reason = "external_or_disallowed_candidate"
                    if reason is None and target["depth"] >= policy.max_depth:
                        reason = "depth_limit"
                    if reason is None and offset >= policy.max_links_per_page:
                        reason = "link_limit"
                    if reason is None and len(state["targets"]) >= policy.max_targets:
                        reason = "target_limit"
                    if reason:
                        boundary = {
                            "parent": target["url"],
                            "url": url,
                            "reason": reason,
                        }
                        if boundary not in state["boundaries"]:
                            state["boundaries"].append(boundary)
                        continue
                    state["targets"].append(
                        _new_target(url, target["depth"] + 1, target["url"])
                    )
                    known.add(url)
        except HTTPError as exc:
            exc.close()
            if exc.code in {404, 410}:
                target["status"] = "unavailable"
            elif exc.code in {401, 403}:
                target["status"] = "restricted"
            elif exc.code in {408, 425, 429} or exc.code >= 500:
                target["status"] = (
                    "retryable"
                    if target["attempts"] < policy.max_attempts
                    else "failed"
                )
            else:
                target["status"] = "failed"
            target["error"] = {"type": "HTTPError", "status": exc.code}
        except (URLError, TimeoutError, OSError) as exc:
            target["status"] = (
                "retryable" if target["attempts"] < policy.max_attempts else "failed"
            )
            target["error"] = {"type": type(exc).__name__}
        except ValueError as exc:
            target["status"] = "oversized" if "max_bytes" in str(exc) else "failed"
            target["error"] = {"type": type(exc).__name__, "reason": str(exc)}
        state["generation"] += 1
        state = sealed(state)
        atomic_json(state_path, state)
    # Also persist a first-run empty progress checkpoint if all records were terminal.
    atomic_json(state_path, state)
    validate_state(state, policy, root)
    return sealed({
        "schema_version": "1.0",
        "kind": "crawl-readiness",
        **crawl_readiness(state),
    })
