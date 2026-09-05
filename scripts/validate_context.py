"""Reconcile Conductor context, qualification contracts and source registries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


import hashlib
import re
import tomllib
from pathlib import Path
from typing import cast

from australian_health_policy_atlas.authorities import (
    assert_directory_coverage,
    load_authorities,
    load_contract,
)
from australian_health_policy_atlas.microtasks import (
    MAX_EVIDENCE_TOKENS,
    MAX_INSTRUCTION_TOKENS,
)
from australian_health_policy_atlas.records import (
    array,
    decode_json,
    integer,
    record,
    records,
    string,
    strings,
)

ROOT = Path(__file__).resolve().parents[1]
PINNED_ACTION_RE = re.compile(r"uses:\s+[^@\s]+@([^\s#]+)")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load_toml(path: Path) -> dict[str, object]:
    """Load a TOML object for explicit downstream context-contract validation.

    Returns:
        A string-keyed mapping whose values still require schema validation.

    """
    with path.open("rb") as handle:
        return record(cast("object", tomllib.load(handle)))


def load_json(path: Path) -> dict[str, object]:
    """Decode a JSON object without trusting its field types.

    Returns:
        A string-keyed mapping of decoded, untrusted field values.

    """
    return record(decode_json(path.read_text(encoding="utf-8")))


def validate_microtask(errors: list[str]) -> None:
    """Check bounded task configuration and the hash-bound executable example."""
    config = load_toml(ROOT / ".context/tiny-models.toml")
    principles = record(config.get("principles", {}))
    required_true = {
        "model_never_owns_workflow_state",
        "model_never_selects_unbounded_methods",
        "single_open_question_per_call",
        "schema_constrained_output",
        "programmatic_verification_after_every_call",
        "no_hidden_memory_dependency",
    }
    errors.extend(
        f"tiny-model principle must be true: {key}"
        for key in required_true
        if principles.get(key) is not True
    )

    packet = record(config.get("packet", {}))
    if integer(packet.get("max_instruction_tokens", 10_000)) > MAX_INSTRUCTION_TOKENS:
        errors.append("tiny-model instruction budget exceeds 900 tokens")
    if integer(packet.get("max_evidence_tokens_hard", 10_000)) > MAX_EVIDENCE_TOKENS:
        errors.append("tiny-model hard evidence budget exceeds 6000 tokens")

    expected_route = [
        "deterministic_rule",
        "lexical_or_structural_model",
        "tiny_local_model",
        "small_local_model",
        "independent_model_triangulation",
        "larger_model_fallback",
    ]
    if record(config.get("routing", {})).get("order") != expected_route:
        errors.append(
            "tiny-model routing order drifted from deterministic-first contract"
        )

    _validate_example(errors)


def _validate_example(errors: list[str]) -> None:
    schema = load_json(ROOT / "schemas/microtask-packet-v1.json")
    state_schema = load_json(ROOT / "schemas/work-item-state-v1.json")
    if schema.get("additionalProperties") is not False:
        errors.append("microtask schema must fail closed on additional properties")
    if state_schema.get("additionalProperties") is not False:
        errors.append(
            "work-item state schema must fail closed on additional properties"
        )

    example = load_json(ROOT / "examples/microtask-packet.example.json")
    required = set(strings(schema.get("required", [])))
    missing = required - set(example)
    if missing:
        errors.append(f"microtask example missing fields: {sorted(missing)}")
    if len(array(example.get("evidence_refs", []))) != 1:
        errors.append(
            "microtask example must demonstrate a single minimal evidence bundle"
        )
    for evidence in records(example.get("evidence_refs", [])):
        digest = string(evidence.get("sha256", ""))
        text = string(evidence.get("text", ""))
        if not SHA256_RE.fullmatch(digest):
            errors.append("microtask example evidence sha256 is malformed")
        elif hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
            errors.append("microtask example evidence sha256 does not match text")


def validate_ci(errors: list[str]) -> None:
    """Reconcile runtime, toolchain and workflow invariants against project context."""
    ci = load_toml(ROOT / ".context/ci.toml")
    tools = load_json(ROOT / "quality/tool-versions.json")
    python_version = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    if ci.get("python") != python_version or tools.get("python") != python_version:
        errors.append(
            "Python version drift across ci.toml/.python-version/tool-versions.json"
        )
    if ci.get("uv") != tools.get("uv"):
        errors.append("uv version drift across ci.toml/tool-versions.json")

    pyproject = load_toml(ROOT / "pyproject.toml")
    if "3.14" not in string(
        record(pyproject.get("project", {})).get("requires-python", "")
    ):
        errors.append("pyproject must target Python 3.14")
    runtime_deps = record(pyproject.get("project", {})).get("dependencies", [])
    if runtime_deps and not (ROOT / "uv.lock").exists():
        errors.append("runtime dependencies adopted without required uv.lock")

    workflows = {
        "context-ci.yml",
        "dependency-review.yml",
        "security-context.yml",
    }
    workflow_dir = ROOT / ".github/workflows"
    missing_workflows = workflows - {path.name for path in workflow_dir.glob("*.yml")}
    errors.extend(
        f"missing required GitHub workflow: {missing}" for missing in missing_workflows
    )
    _validate_workflows(errors, workflow_dir)
    if 'extends": [\n    "github>edithatogo/renovate-config"' not in (
        ROOT / "renovate.json"
    ).read_text(encoding="utf-8"):
        errors.append("Renovate must inherit edithatogo/renovate-config")


def _validate_workflows(errors: list[str], workflow_dir: Path) -> None:
    for name in sorted(path.name for path in workflow_dir.glob("*.yml")):
        path = workflow_dir / name
        if not path.exists():
            errors.append(f"missing required GitHub workflow: {name}")
            continue
        text = path.read_text(encoding="utf-8")
        for match in PINNED_ACTION_RE.finditer(text):
            ref = match.group(1)
            if not SHA40_RE.fullmatch(ref):
                errors.append(
                    f"workflow action not pinned by commit SHA in {name}: {ref}"
                )
        if "actions/checkout@" in text and "persist-credentials: false" not in text:
            errors.append(f"checkout credentials not disabled in {name}")


def validate_public_corpus(errors: list[str]) -> None:
    """Validate the frozen source-surface inventory and its completion receipt."""
    registry_path = ROOT / "data/sources/source-surfaces-v1.json"
    completion_path = ROOT / "evidence/public-corpus/source-census-v1/completion.json"
    if not registry_path.exists() or not completion_path.exists():
        errors.append("Source Census v1 registry/completion receipt missing")
        return
    registry = load_json(registry_path)
    sources = records(registry.get("sources", []))
    jurisdictions = {string(item.get("jurisdiction")) for item in sources}
    expected = {"QLD", "NSW", "VIC", "SA", "WA", "TAS", "ACT", "NT"}
    if not expected.issubset(jurisdictions):
        errors.append(
            "Source Census v1 missing jurisdictions: "
            f"{sorted(expected - jurisdictions)}"
        )
    if "Cth" not in jurisdictions:
        errors.append("Source Census v1 missing Commonwealth comparator")
    required = {"source_id", "jurisdiction", "url", "capture_adapter", "disposition"}
    for index, item in enumerate(sources):
        missing = required - set(item)
        if missing:
            errors.append(f"source surface {index} missing fields: {sorted(missing)}")
        if not str(item.get("url", "")).startswith("https://"):
            errors.append(f"source surface must use HTTPS: {item.get('source_id')}")
    _validate_corpus_receipts(errors, registry_path, completion_path)


def _validate_corpus_receipts(
    errors: list[str], registry_path: Path, completion_path: Path
) -> None:
    completion = load_json(completion_path)
    actual_sha = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    if completion.get("registry_sha256") != actual_sha:
        errors.append("Source Census v1 completion receipt registry hash drifted")
    if completion.get("status") != "qualified":
        errors.append("Source Census v1 completion receipt is not qualified")

    shadow = ROOT / "quality/shadow/clinical-governance-v0/receipt.json"
    if shadow.exists():
        receipt = load_json(shadow)
        if receipt.get("not_a_medallion_release") is not True:
            errors.append("shadow clinical-governance output must remain non-release")
    readiness = ROOT / "evidence/public-corpus/bronze-v1/readiness.json"
    if readiness.exists():
        bronze = load_json(readiness)
        if (
            bronze.get("gate_b_passed") is not False
            and bronze.get("original_payloads_captured", 0) == 0
        ):
            errors.append("Bronze Gate B cannot pass with zero original payloads")


def validate_required_paths(errors: list[str], project: Mapping[str, object]) -> None:
    """Require every declared context document and manifest to exist."""
    errors.extend(
        f"missing required context: {rel}"
        for rel in strings(project.get("required_context", []))
        if not (ROOT / rel).exists()
    )
    errors.extend(
        f"missing required manifest: {rel}"
        for rel in strings(project.get("required_manifests", []))
        if not (ROOT / rel).exists()
    )


def validate_graph_contract(errors: list[str]) -> None:
    """Require non-authoritative projections and optional NLP dependencies."""
    nlp_graph = load_toml(ROOT / ".context/nlp-graph.toml")
    if record(nlp_graph.get("graph", {})).get("authoritative") is not False:
        errors.append("policy graph must remain non-authoritative")
    if (
        record(nlp_graph.get("graph", {})).get("graph_proximity_can_promote_claim")
        is not False
    ):
        errors.append("graph proximity must not promote claims")
    if (
        record(nlp_graph.get("spacy", {})).get("rule_only_is_independent_method")
        is not False
    ):
        errors.append("rule-only spaCy must not count as independent triangulation")
    if record(nlp_graph.get("graphrag", {})).get("candidate_only") is not True:
        errors.append("GraphRAG must remain candidate-only")
    pyproject = load_toml(ROOT / "pyproject.toml")
    nlp_dependencies = strings(
        record(
            record(pyproject.get("project", {})).get("optional-dependencies", {})
        ).get("nlp", [])
    )
    if not any(item.startswith("spacy>=3.8.16") for item in nlp_dependencies):
        errors.append(
            "spaCy optional dependency must retain Python-3.14-capable baseline"
        )


def validate_ecosystem(errors: list[str]) -> None:
    """Require the canonical reusable dependencies and rcagent archetype."""
    deps = load_toml(ROOT / ".context/dependencies.toml")
    ids = {
        string(dependency.get("id"))
        for dependency in records(deps.get("dependency", []))
    }
    errors.extend(
        f"missing required dependency: {required}"
        for required in ("sourceright", "citeweft", "authentext")
        if required not in ids
    )

    ecosystem = load_toml(ROOT / ".context/ecosystem.toml")
    ecosystem_ids = {
        string(item.get("id")) for item in records(ecosystem.get("github", []))
    }
    if "rcagent" not in ecosystem_ids:
        errors.append("rcagent reuse archetype missing from ecosystem registry")


def validate_autonomy(errors: list[str], project: Mapping[str, object]) -> None:
    """Keep confidence levels and the minimal-approval contract consistent."""
    autonomy = load_toml(ROOT / ".context/autonomy.toml")
    levels = {string(level.get("id")) for level in records(autonomy.get("level", []))}
    if levels != {"A0", "A1", "A2", "A3", "A4"}:
        errors.append("autonomy manifest must define exactly A0-A4")
    if not record(autonomy.get("principles", {})).get("minimal_approval_spam", False):
        errors.append("autonomy manifest must enforce minimal approval spam")
    forbidden_routine_gates = {
        "licensing",
        "public-release",
        "consequential-interpretation",
        "policy-recommendation",
    }
    configured_gates = set(strings(project.get("human_gates", [])))
    bad = forbidden_routine_gates & configured_gates
    if bad:
        errors.append(f"routine approval gates reintroduced: {sorted(bad)}")


def _validate_track(
    errors: list[str], track: Mapping[str, object], track_ids: set[str]
) -> None:
    base = ROOT / string(track["path"])
    errors.extend(
        f"track {track['id']} missing {name}"
        for name in ("spec.md", "plan.md", "metadata.toml")
        if not (base / name).exists()
    )
    metadata_path = base / "metadata.toml"
    if metadata_path.exists():
        metadata = load_toml(metadata_path)
        if (
            metadata.get("id") != track["id"]
            or metadata.get("status") != track["status"]
        ):
            errors.append(f"track {track['id']} metadata disagrees with registry")
    errors.extend(
        f"track {track['id']} has unknown dependency: {dependency}"
        for dependency in strings(track.get("depends_on", []))
        if dependency not in track_ids
    )


def validate_tracks(errors: list[str]) -> None:
    """Check local/central track metadata and sequential medallion prerequisites."""
    registry = load_toml(ROOT / "conductor/registry.toml")
    tracks = records(registry.get("track", []))
    track_ids = {string(track.get("id")) for track in tracks}
    track_status = {
        string(track.get("id")): string(track.get("status")) for track in tracks
    }
    for track in tracks:
        _validate_track(errors, track, track_ids)

    sequence = [("T02", "T03"), ("T03", "T04"), ("T04", "T05")]
    started = {"active", "completed"}
    errors.extend(
        (
            f"medallion gate violation: {downstream} started before "
            f"{upstream} completed"
            for upstream, downstream in sequence
            if track_status.get(downstream) in started
            and track_status.get(upstream) != "completed"
        )
    )

    if not (ROOT / "conductor/completion.md").exists():
        errors.append("missing discrete completion contract")


def main() -> int:
    """Reconcile all context contracts; return failure on any unmet invariant.

    Returns:
        Zero on success; a nonzero process status on a blocked or failed operation.

    """
    errors: list[str] = []
    project_path = ROOT / ".context/project.toml"
    if not project_path.exists():
        print("ERROR missing .context/project.toml")
        return 1
    project = load_toml(project_path)
    validate_required_paths(errors, project)
    validate_graph_contract(errors)
    validate_ecosystem(errors)
    validate_autonomy(errors, project)
    validate_tracks(errors)
    validate_microtask(errors)
    validate_ci(errors)
    validate_public_corpus(errors)
    try:
        assert_directory_coverage(
            load_authorities(ROOT / "data/sources"),
            load_contract(ROOT / "data/sources"),
        )
    except (ValueError, OSError, KeyError, TypeError) as exc:
        errors.append(f"ANZ authority registry invalid: {exc}")

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print("OK context, autonomy, tiny-model, CI and Conductor reconciliation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
