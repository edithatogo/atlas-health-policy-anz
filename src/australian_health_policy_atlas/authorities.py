"""Typed ANZ source authority registry; registration is never corpus qualification.

Directory membership is checked against separate, explicit membership contracts.
Bodies, their acquisition surfaces, statutory functions and document applicability
are different objects. Country selection is a retrieval scope, not legal advice.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import defaultdict
from datetime import date
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .crawl import CrawlPolicy, check_url
from .integrity import IDENTIFIER, read_json, sealed
from .source_registry import JURISDICTIONS

ROLES = frozenset({
    "professional_regulator",
    "education_accreditor",
    "accreditation_committee",
    "professional_standard_setter",
    "service_accreditor",
    "sector_regulator",
    "standard_setter",
    "rights_oversight",
    "policy_issuer",
    "funding_authority",
    "advisory_committee",
    "ethics_committee",
    "accreditation_body",
    "legislation_publisher",
})
FIELDS = (
    "body_id",
    "name",
    "countries",
    "jurisdiction",
    "role",
    "url",
    "groups",
    "topics",
)
COLLECTIONS = ("au-v1", "nz-v1", "authorities-v1", "anz-v1")


def source_bytes(name: str, directory: Path | None = None) -> bytes:
    """Read a governed basename from a checkout or portable application."""
    if Path(name).name != name or name.startswith("."):
        raise ValueError("registry basename required")
    if directory is not None:
        path = directory / name
        if path.is_symlink():
            raise ValueError("registry symlink forbidden")
        return path.read_bytes()
    bundled = files("australian_health_policy_atlas").joinpath("_data", name)
    if bundled.is_file():
        return bundled.read_bytes()
    return (
        Path(__file__).resolve().parents[2] / "data" / "sources" / name
    ).read_bytes()


def load_authorities(directory: Path | None = None) -> list[dict[str, Any]]:
    reader = csv.DictReader(
        io.StringIO(source_bytes("authorities-anz-v1.csv", directory).decode("utf-8"))
    )
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("authority columns must match the versioned contract")
    records = []
    for row in reader:
        if set(row) != set(FIELDS) or any(
            not isinstance(v, str) or not v.strip() for v in row.values()
        ):
            raise ValueError("missing or extra authority fields")
        record = dict(row)
        for key in ("countries", "groups", "topics"):
            record[key] = row[key].split(";")
        records.append(record)
    validate_authorities(records)
    return records


def validate_authorities(records: list[dict[str, Any]]) -> None:
    if not records:
        raise ValueError("authority registry cannot be empty")
    identities = set()
    for row in records:
        identity = row.get("body_id", "")
        if (
            not isinstance(identity, str)
            or not IDENTIFIER.fullmatch(identity)
            or identity in identities
        ):
            raise ValueError("invalid or duplicate body identity")
        identities.add(identity)
        if row.get("role") not in ROLES or row.get("jurisdiction") not in JURISDICTIONS:
            raise ValueError("unknown role or jurisdiction")
        countries = row.get("countries")
        if (
            not isinstance(countries, list)
            or not countries
            or len(set(countries)) != len(countries)
            or not set(countries) <= {"AU", "NZ"}
        ):
            raise ValueError("invalid country scope")
        expected = (
            "ANZ" if len(countries) == 2 else "NZ" if countries == ["NZ"] else None
        )
        if (expected and row["jurisdiction"] != expected) or (
            countries == ["AU"] and row["jurisdiction"] in {"NZ", "ANZ"}
        ):
            raise ValueError("country and source jurisdiction disagree")
        for key in ("groups", "topics"):
            values = row.get(key)
            if (
                not isinstance(values, list)
                or not values
                or len(set(values)) != len(values)
                or any(
                    not isinstance(v, str) or not IDENTIFIER.fullmatch(v)
                    for v in values
                )
            ):
                raise ValueError("invalid grouping or topics")
        url = row.get("url")
        if not isinstance(url, str):
            raise ValueError("official URL required")
        host = urlsplit(url).hostname
        if not host:
            raise ValueError("official host required")
        check_url(url, (host,))


def coverage_report(
    records: list[dict[str, Any]], contract: dict[str, Any]
) -> dict[str, Any]:
    """Report complete named directory sets separately from the open-world corpus."""
    validate_authorities(records)
    if (
        type(contract.get("schema_version")) is not int
        or contract["schema_version"] != 1
        or contract.get("open_world_complete") is not False
    ):
        raise ValueError("invalid authority coverage contract")
    date.fromisoformat(contract["registered_on"])
    actual: dict[str, set[str]] = defaultdict(set)
    for row in records:
        for group in row["groups"]:
            actual[group].add(row["body_id"])
    reports = []
    known = set()
    for group in contract["groups"]:
        identity = group["group_id"]
        if identity in known or not IDENTIFIER.fullmatch(identity):
            raise ValueError("duplicate or invalid group")
        known.add(identity)
        check_url(group["evidence_url"], (urlsplit(group["evidence_url"]).hostname,))
        universe = group["universe"]
        if (
            universe not in {"closed-directory-snapshot", "open"}
            or group.get("document_corpus_complete") is not False
        ):
            raise ValueError("invalid universe or unsupported corpus claim")
        required = group["required_members"]
        if not isinstance(required, list) or len(required) != len(set(required)):
            raise ValueError("invalid independent membership contract")
        closed = universe == "closed-directory-snapshot"
        if closed and (not required or not group.get("observed_on")):
            raise ValueError(
                "closed directory requires observation date and explicit membership"
            )
        if closed:
            date.fromisoformat(group["observed_on"])
        missing = sorted(set(required) - actual[identity])
        unexpected = sorted(actual[identity] - set(required)) if closed else []
        reports.append({
            "group_id": identity,
            "registered": len(actual[identity]),
            "denominator": len(required) if closed else None,
            "denominator_unit": group["denominator_unit"],
            "missing": missing,
            "unexpected": unexpected,
            "status": "matched_directory_snapshot"
            if closed and not missing and not unexpected
            else "directory_mismatch"
            if closed
            else "open_scope",
            "evidence_url": group["evidence_url"],
            "document_corpus_complete": False,
        })
    if set(actual) - known:
        raise ValueError("authority references undeclared coverage group")
    return sealed({
        "schema_version": 1,
        "kind": "authority-registration-coverage",
        "snapshot_id": contract["snapshot_id"],
        "registered_bodies": len(records),
        "groups": reports,
        "open_world_complete": False,
        "gate_b_passed": False,
        "remaining_scope": contract["remaining_scope"],
    })


def load_contract(directory: Path | None = None) -> dict[str, Any]:
    return read_json(source_bytes("authority-coverage-v1.json", directory))


def assert_directory_coverage(
    records: list[dict[str, Any]], contract: dict[str, Any]
) -> dict[str, Any]:
    report = coverage_report(records, contract)
    if any(item["status"] == "directory_mismatch" for item in report["groups"]):
        raise ValueError(
            "authority directory membership drift; update evidence, not just the count"
        )
    return report


def acquisition_sources(
    collection: str = "authorities-v1", directory: Path | None = None
) -> list[dict[str, Any]]:
    """Deduplicate shared official portals without conflating their issuing bodies."""
    if collection not in {"authorities-v1", "nz-v1"}:
        raise ValueError("authority or NZ collection required")
    records = load_authorities(directory)
    contract = load_contract(directory)
    assert_directory_coverage(records, contract)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        if collection == "nz-v1" and "NZ" not in row["countries"]:
            continue
        grouped[row["url"], row["jurisdiction"]].append(row)
    result = []
    for (url, jurisdiction), bodies in sorted(grouped.items()):
        ids = sorted(b["body_id"] for b in bodies)
        result.append({
            "source_id": "authority-" + ids[0],
            "url": url,
            "jurisdiction": jurisdiction,
            "body_ids": ids,
            "countries": sorted({c for b in bodies for c in b["countries"]}),
            "roles": sorted({b["role"] for b in bodies}),
            "registered_on": contract["registered_on"],
            "capture_status": "configured_unqualified",
            "bindingness": "not_inferred",
            "source_scope_not_document_applicability": True,
        })
    return sorted(result, key=lambda x: x["source_id"])


def authority_policies(
    collection: str, directory: Path | None = None
) -> list[CrawlPolicy]:
    policies = []
    for source in acquisition_sources(collection, directory):
        host = urlsplit(source["url"]).hostname
        policy = CrawlPolicy(
            source["source_id"],
            source["jurisdiction"],
            source["url"],
            (host,),
            source["registered_on"] + "T00:00:00Z",
            max_depth=2,
            max_targets=200,
            max_links_per_page=100,
            max_attempts=3,
            policy_version="bounded-authority-discovery-v1",
        )
        policy.validate()
        policies.append(policy)
    return policies


def authority_graph(directory: Path | None = None):
    """Build a catalogue graph without legal or clinical assertion edges."""
    from .graph import GraphEdge, GraphNode, PolicyGraph

    records = load_authorities(directory)
    assert_directory_coverage(records, load_contract(directory))
    graph = PolicyGraph()
    for body in records:
        identity = "authority:" + body["body_id"]
        graph.add_node(GraphNode(identity, "authority", body["name"], body))
        role = "role:" + body["role"]
        graph.add_node(GraphNode(role, "authority_role", body["role"], {}))
        graph.add_edge(
            GraphEdge(
                identity,
                role,
                "REGISTERED_ROLE",
                {"document_bindingness": "not_inferred"},
            )
        )
        for country in body["countries"]:
            node = "country:" + country
            graph.add_node(GraphNode(node, "country", country, {}))
            graph.add_edge(GraphEdge(identity, node, "SELECTED_FOR_COMPARISON", {}))
    for source in acquisition_sources("authorities-v1", directory):
        identity = "source:" + source["source_id"]
        graph.add_node(
            GraphNode(identity, "source_registry_entry", source["url"], source)
        )
        for body in source["body_ids"]:
            graph.add_edge(
                GraphEdge("authority:" + body, identity, "HAS_REGISTERED_SOURCE", {})
            )
    return graph


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--sources", choices=("nz-v1", "authorities-v1"))
    parser.add_argument("--graph", action="store_true")
    args = parser.parse_args(argv)
    result = (
        acquisition_sources(args.sources, args.directory)
        if args.sources
        else assert_directory_coverage(
            load_authorities(args.directory), load_contract(args.directory)
        )
    )
    if args.graph:
        graph = authority_graph(args.directory)
        result = {
            "kind": "authority-catalogue-projection",
            "nodes": [n.as_dict() for n in graph.nodes.values()],
            "edges": [e.as_dict() for e in graph.edges],
            "gate_b_passed": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
