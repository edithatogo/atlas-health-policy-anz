"""Typed ANZ source authority registry; registration is never corpus qualification.

Directory membership is checked against separate, explicit membership contracts.
Bodies, their acquisition surfaces, statutory functions and document applicability
are different objects. Country selection is a retrieval scope, not legal advice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from datetime import date
from importlib.resources import files
from operator import itemgetter
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlsplit

from .crawl import CrawlPolicy, check_url
from .graph import GraphEdge, GraphNode, PolicyGraph
from .integrity import IDENTIFIER, read_json, sealed
from .records import records as object_records
from .records import string, strings
from .source_registry import JURISDICTIONS

JOINT_COUNTRY_COUNT = 2


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
    """Read a governed basename from a checkout or portable application.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: Source scope, identity or resource-budget validation fails.

    """
    if Path(name).name != name or name.startswith("."):
        message = "registry basename required"
        raise ValueError(message)
    if directory is not None:
        path = directory / name
        if path.is_symlink():
            message = "registry symlink forbidden"
            raise ValueError(message)
        return path.read_bytes()
    bundled = files("australian_health_policy_atlas").joinpath("_data", name)
    if bundled.is_file():
        return bundled.read_bytes()
    return (
        Path(__file__).resolve().parents[2] / "data" / "sources" / name
    ).read_bytes()


class AuthorityRecord(TypedDict):
    """One validated issuing-body identity with independent acquisition scope."""

    body_id: str
    name: str
    countries: list[str]
    jurisdiction: str
    role: str
    url: str
    groups: list[str]
    topics: list[str]


class AcquisitionSource(TypedDict):
    """One deduplicated acquisition surface retaining all issuing-body identities."""

    source_id: str
    url: str
    jurisdiction: str
    body_ids: list[str]
    countries: list[str]
    roles: list[str]
    registered_on: str
    capture_status: str
    bindingness: str
    source_scope_not_document_applicability: bool


def _body(row: Mapping[str, object]) -> AuthorityRecord:
    return AuthorityRecord(
        body_id=string(row["body_id"]),
        name=string(row["name"]),
        countries=strings(row["countries"]),
        jurisdiction=string(row["jurisdiction"]),
        role=string(row["role"]),
        url=string(row["url"]),
        groups=strings(row["groups"]),
        topics=strings(row["topics"]),
    )


def load_authorities(directory: Path | None = None) -> list[AuthorityRecord]:
    """Read and validate every authority row against the explicit field contract.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: CSV columns or required fields differ from the contract.

    """
    reader = csv.DictReader(
        io.StringIO(source_bytes("authorities-anz-v1.csv", directory).decode("utf-8"))
    )
    if tuple(reader.fieldnames or ()) != FIELDS:
        message = "authority columns must match the versioned contract"
        raise ValueError(message)
    result: list[AuthorityRecord] = []
    for row in reader:
        if set(row) != set(FIELDS) or any(
            not isinstance(value, str) or not value.strip() for value in row.values()
        ):
            message = "missing or extra authority fields"
            raise ValueError(message)
        fields: dict[str, object] = dict(row)
        for key in ("countries", "groups", "topics"):
            fields[key] = string(row[key]).split(";")
        result.append(_body(fields))
    validate_authorities(result)
    return result


def _country_scope(row: Mapping[str, object]) -> None:
    countries = strings(row.get("countries"))
    if (
        not countries
        or len(set(countries)) != len(countries)
        or not set(countries) <= {"AU", "NZ"}
    ):
        message = "invalid country scope"
        raise ValueError(message)
    expected = (
        "ANZ"
        if len(countries) == JOINT_COUNTRY_COUNT
        else "NZ"
        if countries == ["NZ"]
        else None
    )
    if (expected and row["jurisdiction"] != expected) or (
        countries == ["AU"] and row["jurisdiction"] in {"NZ", "ANZ"}
    ):
        message = "country and source jurisdiction disagree"
        raise ValueError(message)


def _group_scope(row: Mapping[str, object]) -> None:
    for key in ("groups", "topics"):
        values = strings(row.get(key))
        if (
            not values
            or len(set(values)) != len(values)
            or any(not IDENTIFIER.fullmatch(value) for value in values)
        ):
            message = "invalid grouping or topics"
            raise ValueError(message)


def _official_host(url: str) -> str:
    host = urlsplit(url).hostname
    if not host:
        message = "official host required"
        raise ValueError(message)
    check_url(url, (host,))
    return host


def validate_authorities(rows: Sequence[Mapping[str, object]]) -> None:
    """Validate identity, retrieval scope and authority-role metadata.

    Raises:
        ValueError: The registry is empty, duplicated or has invalid scope fields.

    """
    if not rows:
        message = "authority registry cannot be empty"
        raise ValueError(message)
    identities: set[str] = set()
    for row in rows:
        identity = string(row.get("body_id", ""))
        if not IDENTIFIER.fullmatch(identity) or identity in identities:
            message = "invalid or duplicate body identity"
            raise ValueError(message)
        identities.add(identity)
        if row.get("role") not in ROLES or row.get("jurisdiction") not in JURISDICTIONS:
            message = "unknown role or jurisdiction"
            raise ValueError(message)
        _country_scope(row)
        _group_scope(row)
        _official_host(string(row.get("url")))


def _coverage_group(group: Mapping[str, object], actual: set[str]) -> dict[str, object]:
    identity = string(group["group_id"])
    url = string(group["evidence_url"])
    _official_host(url)
    universe = group["universe"]
    if (
        universe not in {"closed-directory-snapshot", "open"}
        or group.get("document_corpus_complete") is not False
    ):
        message = "invalid universe or unsupported corpus claim"
        raise ValueError(message)
    required = strings(group["required_members"])
    if len(required) != len(set(required)):
        message = "invalid independent membership contract"
        raise ValueError(message)
    closed = universe == "closed-directory-snapshot"
    if closed and (not required or not group.get("observed_on")):
        message = "closed directory requires observation date and explicit membership"
        raise ValueError(message)
    if closed:
        date.fromisoformat(string(group["observed_on"]))
    missing = sorted(set(required) - actual)
    unexpected = sorted(actual - set(required)) if closed else []
    return {
        "group_id": identity,
        "registered": len(actual),
        "denominator": len(required) if closed else None,
        "denominator_unit": group["denominator_unit"],
        "missing": missing,
        "unexpected": unexpected,
        "status": "matched_directory_snapshot"
        if closed and not missing and not unexpected
        else "directory_mismatch"
        if closed
        else "open_scope",
        "evidence_url": url,
        "document_corpus_complete": False,
    }


def coverage_report(
    records: Sequence[Mapping[str, object]], contract: Mapping[str, object]
) -> dict[str, object]:
    """Report named directory membership separately from open-world coverage.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: The contract is invalid or contains undeclared groups.

    """
    validate_authorities(records)
    if (
        type(contract.get("schema_version")) is not int
        or contract["schema_version"] != 1
        or contract.get("open_world_complete") is not False
    ):
        message = "invalid authority coverage contract"
        raise ValueError(message)
    date.fromisoformat(string(contract["registered_on"]))
    actual: dict[str, set[str]] = defaultdict(set)
    for row in records:
        for group in strings(row["groups"]):
            actual[group].add(string(row["body_id"]))
    reports: list[dict[str, object]] = []
    known: set[str] = set()
    for group in object_records(contract["groups"]):
        identity = string(group["group_id"])
        if identity in known or not IDENTIFIER.fullmatch(identity):
            message = "duplicate or invalid group"
            raise ValueError(message)
        known.add(identity)
        reports.append(_coverage_group(group, actual[identity]))
    if set(actual) - known:
        message = "authority references undeclared coverage group"
        raise ValueError(message)
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


def load_contract(directory: Path | None = None) -> dict[str, object]:
    """Load the authority coverage contract without assuming its assertions are true.

    Returns:
        The decoded coverage contract for explicit membership validation.

    """
    return read_json(source_bytes("authority-coverage-v1.json", directory))


def assert_directory_coverage(
    records: Sequence[Mapping[str, object]], contract: Mapping[str, object]
) -> dict[str, object]:
    """Check exact membership of each closed official-directory snapshot.

    Returns:
        The coverage report when all closed membership contracts match.

    Raises:
        ValueError: The supplied data violates the function's documented validation
        contract.

    """
    report = coverage_report(records, contract)
    if any(
        item["status"] == "directory_mismatch"
        for item in object_records(report["groups"])
    ):
        message = (
            "authority directory membership drift; update evidence, not just the count"
        )
        raise ValueError(message)
    return report


def acquisition_sources(
    collection: str = "authorities-v1", directory: Path | None = None
) -> list[AcquisitionSource]:
    """Deduplicate shared official portals without conflating their issuing bodies.

    Returns:
        The result described above, retaining the declared return-type contract.

    Raises:
        ValueError: Source scope, identity or resource-budget validation fails.

    """
    if collection not in {"authorities-v1", "nz-v1"}:
        message = "authority or NZ collection required"
        raise ValueError(message)
    records = load_authorities(directory)
    contract = load_contract(directory)
    assert_directory_coverage(records, contract)
    grouped: dict[tuple[str, str], list[AuthorityRecord]] = defaultdict(list)
    for row in records:
        if collection == "nz-v1" and "NZ" not in row["countries"]:
            continue
        grouped[row["url"], row["jurisdiction"]].append(row)
    result: list[AcquisitionSource] = []
    for (url, jurisdiction), bodies in sorted(grouped.items()):
        ids = sorted(b["body_id"] for b in bodies)
        result.append({
            "source_id": "authority-" + ids[0],
            "url": url,
            "jurisdiction": jurisdiction,
            "body_ids": ids,
            "countries": sorted({c for b in bodies for c in b["countries"]}),
            "roles": sorted({b["role"] for b in bodies}),
            "registered_on": string(contract["registered_on"]),
            "capture_status": "configured_unqualified",
            "bindingness": "not_inferred",
            "source_scope_not_document_applicability": True,
        })
    return sorted(result, key=itemgetter("source_id"))


def authority_policies(
    collection: str, directory: Path | None = None
) -> list[CrawlPolicy]:
    """Create bounded crawl profiles for the selected authority collection.

    Returns:
        Validated finite crawl policies for the selected acquisition surfaces.

    """
    policies: list[CrawlPolicy] = []
    for source in acquisition_sources(collection, directory):
        host = _official_host(source["url"])
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


def authority_graph(directory: Path | None = None) -> PolicyGraph:
    """Build a catalogue graph without legal or clinical assertion edges.

    Returns:
        The result described above, retaining the declared return-type contract.

    """
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


class Arguments(argparse.Namespace):
    """Closed, typed argument surface for catalogue inspection."""

    directory: Path | None = None
    sources: str | None = None
    graph: bool = False


def main(argv: list[str] | None = None) -> int:
    """Report registered authorities, acquisition surfaces or derived graph metadata.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--sources", choices=("nz-v1", "authorities-v1"))
    parser.add_argument("--graph", action="store_true")
    args = parser.parse_args(argv, namespace=Arguments())
    result: object = (
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
    sys.stdout.write(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
