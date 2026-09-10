"""Nine governed seed-only access probes, independent of Hub credentials.

Bounded access observations are not full discovery, policy currency, corpus
coverage or Bronze closure. Raw responses stay in short-lived replay bundles.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from .capture_bundle import export_bundle, restore_bundle
from .capture_plan import compile_plan
from .crawl import CrawlPolicy, run_crawl
from .hashing import canonical_json_bytes, sha256_json
from .hub_staging import build_stage
from .integrity import atomic_json, read_json, sealed
from .operations import load_collection
from .packet_ingestion import require_packet
from .records import integer, record, records

if TYPE_CHECKING:
    from .capture import CapturePort

SEEDS = (
    "act-health-policies",
    "nsw-policy-home",
    "nt-health-professionals",
    "qld-policies-standards-root",
    "sa-policy-governance",
    "tas-health-root",
    "vic-health-policies-guidelines",
    "wa-policy-frameworks",
    "authority-nz-moh",
)
PROBE_LINKS = 10
PROBE_BYTES = 1024 * 1024


def probe_policies() -> tuple[list[CrawlPolicy], dict[str, str]]:
    """Derive a diagnostic selection without modifying the governed source registry.

    Returns:
        Probe identities and independent parent-policy hashes. The inherited
        inventory cutoff is not the timestamp of any actual HTTP observation.

    """
    source_list = load_collection("anz-v1")
    sources = {p.source_id: p for p in source_list}
    require_packet(len(sources) == len(source_list), "duplicate governed source")
    require_packet(set(SEEDS) <= sources.keys(), "governed probe source missing")
    parents: dict[str, str] = {}
    policies: list[CrawlPolicy] = []
    for identity in sorted(SEEDS):
        source = sources[identity]
        probe = replace(
            source,
            source_id="probe-" + identity,
            policy_version="bounded-seed-probe-v1",
            max_depth=0,
            max_targets=1,
            max_attempts=1,
            max_links_per_page=PROBE_LINKS,
            max_bytes=PROBE_BYTES,
        )
        probe.validate()
        policies.append(probe)
        parents[probe.source_id] = sha256_json(source.as_dict())
    return policies, parents


def plan_probe() -> dict[str, object]:
    """Compile a secret-free diagnostic plan bound to exact source configuration.

    Returns:
        One frontier attempt and at most 1 MiB captured body per seed. Redirects,
        TLS traffic and runner duration are not part of the body-byte budget.

    """
    policies, parents = probe_policies()
    plan = sealed({
        **compile_plan(policies, "seed-probe-v1", 1),
        "kind": "governed-seed-probe-plan",
        "parent_source_policy_hashes": parents,
        "policies": [p.as_dict() for p in policies],
        "maximum_captured_body_bytes": len(policies) * PROBE_BYTES,
        "scope": "seed_access_only_not_document_discovery",
        "temporary_artifacts_are_not_canonical_storage": True,
        "hf_publication_attempted": False,
    })
    return read_json(canonical_json_bytes(plan))


def probe_one(
    policy: CrawlPolicy, root: Path, *, fetch: CapturePort | None = None
) -> dict[str, object]:
    """Capture one bounded seed, export its stage and independently replay it.

    Returns:
        The actual capture disposition and portable archive reference. Failed
        access attempts remain in state, never inferred to mean absent policies.

    """
    require_packet(
        policy.policy_version == "bounded-seed-probe-v1"
        and policy.max_depth == 0
        and policy.max_targets == policy.max_attempts == 1
        and policy.max_links_per_page == PROBE_LINKS
        and policy.max_bytes == PROBE_BYTES,
        "seed probe requires its exact narrow limits",
    )
    require_packet(not root.exists() and not root.is_symlink(), "probe root exists")
    root.mkdir(parents=True)
    with TemporaryDirectory(prefix="atlas-probe-") as directory:
        scratch = Path(directory)
        readiness = (
            run_crawl(policy, scratch / "crawl", request_budget=1, fetch=fetch)
            if fetch is not None
            else run_crawl(policy, scratch / "crawl", request_budget=1)
        )
        manifest = build_stage(scratch / "crawl", scratch / "stage")
        reference = export_bundle(scratch / "stage", root / "capture.zip", policy)
        restored = restore_bundle(
            root / "capture.zip", reference, policy, scratch / "replayed"
        )
        require_packet(restored == manifest, "probe reconstruction mismatch")
    atomic_json(root / "reference.json", reference)
    return sealed({
        "source_id": policy.source_id,
        "jurisdiction": policy.jurisdiction,
        "readiness": readiness,
        "reference": reference,
        "bundle_reconstruction_verified": True,
        "hf_publication_attempted": False,
        "policy_semantics_qualified": False,
        "gate_b_passed": False,
    })


def run_probe(output: Path, *, fetch: CapturePort | None = None) -> dict[str, object]:
    """Execute the registered diagnostic with a durable, full selected denominator.

    Returns:
        A sealed run observation. Interruptions leave an incomplete journal;
        ordinary source access failures are retained as terminal crawl states.
        Exceptions stop the run rather than creating a false completion claim.

    """
    plan = plan_probe()
    require_packet(not output.exists() and not output.is_symlink(), "output exists")
    output.mkdir(parents=True)
    atomic_json(output / "plan.json", plan)
    observed: list[dict[str, object]] = []

    def persist(*, complete: bool) -> dict[str, object]:
        result = sealed({
            "schema_version": "1.0",
            "kind": "governed-seed-probe-run",
            "plan_sha256": plan["sha256"],
            "selected_source_ids": ["probe-" + identity for identity in sorted(SEEDS)],
            "observations": observed,
            "execution_complete": complete,
            "captured_source_count": sum(
                integer(record(record(i["readiness"])["counts"])["captured"])
                for i in observed
            ),
            "hf_publication_attempted": False,
            "not_medallion_release": True,
            "gate_b_passed": False,
        })
        atomic_json(output / "run.json", result)
        return result

    persist(complete=False)
    for row in records(plan["policies"]):
        policy = CrawlPolicy.from_record(row)
        observed.append(probe_one(policy, output / policy.source_id, fetch=fetch))
        persist(complete=False)
    return persist(complete=True)


class Arguments(argparse.Namespace):
    """Fixed plan/run operation and fresh output directory, never arbitrary URLs."""

    mode: str = "plan"
    output: Path = Path("build/seed-probe")


def main(argv: list[str] | None = None) -> int:
    """Plan offline or execute the governed public diagnostic without credentials.

    Returns:
        Zero for completed execution, including explicit source access failures.
        Capture counts, not exit status, describe successfully retrieved bodies.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    parser.add_argument("--output", type=Path, default=Path("build/seed-probe"))
    args = parser.parse_args(argv, namespace=Arguments())
    if args.mode == "plan":
        result = plan_probe()
        require_packet(not args.output.exists(), "output exists")
        atomic_json(args.output / "plan.json", result)
    else:
        result = run_probe(args.output)
    sys.stdout.buffer.write(canonical_json_bytes(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
