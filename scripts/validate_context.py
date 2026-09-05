from __future__ import annotations

import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PINNED_ACTION_RE = re.compile(r"uses:\s+[^@\s]+@([^\s#]+)")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_microtask(errors: list[str]) -> None:
    config = load_toml(ROOT / ".context/tiny-models.toml")
    principles = config.get("principles", {})
    required_true = {
        "model_never_owns_workflow_state",
        "model_never_selects_unbounded_methods",
        "single_open_question_per_call",
        "schema_constrained_output",
        "programmatic_verification_after_every_call",
        "no_hidden_memory_dependency",
    }
    for key in required_true:
        if principles.get(key) is not True:
            errors.append(f"tiny-model principle must be true: {key}")

    packet = config.get("packet", {})
    if packet.get("max_instruction_tokens", 10_000) > 900:
        errors.append("tiny-model instruction budget exceeds 900 tokens")
    if packet.get("max_evidence_tokens_hard", 10_000) > 6000:
        errors.append("tiny-model hard evidence budget exceeds 6000 tokens")

    expected_route = [
        "deterministic_rule",
        "lexical_or_structural_model",
        "tiny_local_model",
        "small_local_model",
        "independent_model_triangulation",
        "larger_model_fallback",
    ]
    if config.get("routing", {}).get("order") != expected_route:
        errors.append(
            "tiny-model routing order drifted from deterministic-first contract"
        )

    schema = load_json(ROOT / "schemas/microtask-packet-v1.json")
    state_schema = load_json(ROOT / "schemas/work-item-state-v1.json")
    if schema.get("additionalProperties") is not False:
        errors.append("microtask schema must fail closed on additional properties")
    if state_schema.get("additionalProperties") is not False:
        errors.append(
            "work-item state schema must fail closed on additional properties"
        )

    example = load_json(ROOT / "examples/microtask-packet.example.json")
    required = set(schema.get("required", []))
    missing = required - set(example)
    if missing:
        errors.append(f"microtask example missing fields: {sorted(missing)}")
    if len(example.get("evidence_refs", [])) != 1:
        errors.append(
            "microtask example must demonstrate a single minimal evidence bundle"
        )
    for evidence in example.get("evidence_refs", []):
        digest = evidence.get("sha256", "")
        text = evidence.get("text", "")
        if not SHA256_RE.fullmatch(digest):
            errors.append("microtask example evidence sha256 is malformed")
        elif hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
            errors.append("microtask example evidence sha256 does not match text")


def validate_ci(errors: list[str]) -> None:
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
    if "3.14" not in pyproject.get("project", {}).get("requires-python", ""):
        errors.append("pyproject must target Python 3.14")
    runtime_deps = pyproject.get("project", {}).get("dependencies", [])
    if runtime_deps and not (ROOT / "uv.lock").exists():
        errors.append("runtime dependencies adopted without required uv.lock")

    workflows = {
        "context-ci.yml",
        "dependency-review.yml",
        "security-context.yml",
    }
    workflow_dir = ROOT / ".github/workflows"
    missing_workflows = workflows - {path.name for path in workflow_dir.glob("*.yml")}
    for missing in missing_workflows:
        errors.append(f"missing required GitHub workflow: {missing}")
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
    if 'extends": [\n    "github>edithatogo/renovate-config"' not in (
        ROOT / "renovate.json"
    ).read_text(encoding="utf-8"):
        errors.append("Renovate must inherit edithatogo/renovate-config")


def validate_public_corpus(errors: list[str]) -> None:
    registry_path = ROOT / "data/sources/source-surfaces-v1.json"
    completion_path = ROOT / "evidence/public-corpus/source-census-v1/completion.json"
    if not registry_path.exists() or not completion_path.exists():
        errors.append("Source Census v1 registry/completion receipt missing")
        return
    registry = load_json(registry_path)
    sources = registry.get("sources", [])
    jurisdictions = {item.get("jurisdiction") for item in sources}
    expected = {"QLD", "NSW", "VIC", "SA", "WA", "TAS", "ACT", "NT"}
    if not expected.issubset(jurisdictions):
        errors.append(
            f"Source Census v1 missing jurisdictions: {sorted(expected - jurisdictions)}"
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


def main() -> int:
    errors: list[str] = []
    project_path = ROOT / ".context/project.toml"
    if not project_path.exists():
        print("ERROR missing .context/project.toml")
        return 1
    project = load_toml(project_path)
    for rel in project.get("required_context", []):
        if not (ROOT / rel).exists():
            errors.append(f"missing required context: {rel}")
    for rel in project.get("required_manifests", []):
        if not (ROOT / rel).exists():
            errors.append(f"missing required manifest: {rel}")

    nlp_graph = load_toml(ROOT / ".context/nlp-graph.toml")
    if nlp_graph.get("graph", {}).get("authoritative") is not False:
        errors.append("policy graph must remain non-authoritative")
    if nlp_graph.get("graph", {}).get("graph_proximity_can_promote_claim") is not False:
        errors.append("graph proximity must not promote claims")
    if nlp_graph.get("spacy", {}).get("rule_only_is_independent_method") is not False:
        errors.append("rule-only spaCy must not count as independent triangulation")
    if nlp_graph.get("graphrag", {}).get("candidate_only") is not True:
        errors.append("GraphRAG must remain candidate-only")
    pyproject = load_toml(ROOT / "pyproject.toml")
    nlp_dependencies = (
        pyproject.get("project", {}).get("optional-dependencies", {}).get("nlp", [])
    )
    if not any(item.startswith("spacy>=3.8.16") for item in nlp_dependencies):
        errors.append(
            "spaCy optional dependency must retain Python-3.14-capable baseline"
        )

    deps = load_toml(ROOT / ".context/dependencies.toml")
    ids = {dependency.get("id") for dependency in deps.get("dependency", [])}
    for required in ("sourceright", "citeweft", "authentext"):
        if required not in ids:
            errors.append(f"missing required dependency: {required}")

    ecosystem = load_toml(ROOT / ".context/ecosystem.toml")
    ecosystem_ids = {item.get("id") for item in ecosystem.get("github", [])}
    if "rcagent" not in ecosystem_ids:
        errors.append("rcagent reuse archetype missing from ecosystem registry")

    autonomy = load_toml(ROOT / ".context/autonomy.toml")
    levels = {level.get("id") for level in autonomy.get("level", [])}
    if levels != {"A0", "A1", "A2", "A3", "A4"}:
        errors.append("autonomy manifest must define exactly A0-A4")
    if not autonomy.get("principles", {}).get("minimal_approval_spam", False):
        errors.append("autonomy manifest must enforce minimal approval spam")
    forbidden_routine_gates = {
        "licensing",
        "public-release",
        "consequential-interpretation",
        "policy-recommendation",
    }
    configured_gates = set(project.get("human_gates", []))
    bad = forbidden_routine_gates & configured_gates
    if bad:
        errors.append(f"routine approval gates reintroduced: {sorted(bad)}")

    registry = load_toml(ROOT / "conductor/registry.toml")
    tracks = registry.get("track", [])
    track_ids = {track.get("id") for track in tracks}
    track_status = {track.get("id"): track.get("status") for track in tracks}
    for track in tracks:
        base = ROOT / track["path"]
        for name in ("spec.md", "plan.md", "metadata.toml"):
            if not (base / name).exists():
                errors.append(f"track {track['id']} missing {name}")
        metadata_path = base / "metadata.toml"
        if metadata_path.exists():
            metadata = load_toml(metadata_path)
            if (
                metadata.get("id") != track["id"]
                or metadata.get("status") != track["status"]
            ):
                errors.append(f"track {track['id']} metadata disagrees with registry")
        for dependency in track.get("depends_on", []):
            if dependency not in track_ids:
                errors.append(
                    f"track {track['id']} has unknown dependency: {dependency}"
                )

    sequence = [("T02", "T03"), ("T03", "T04"), ("T04", "T05")]
    started = {"active", "completed"}
    for upstream, downstream in sequence:
        if (
            track_status.get(downstream) in started
            and track_status.get(upstream) != "completed"
        ):
            errors.append(
                f"medallion gate violation: {downstream} started before {upstream} completed"
            )

    if not (ROOT / "conductor/completion.md").exists():
        errors.append("missing discrete completion contract")

    validate_microtask(errors)
    validate_ci(errors)
    validate_public_corpus(errors)
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from australian_health_policy_atlas.authorities import (
            assert_directory_coverage,
            load_authorities,
            load_contract,
        )

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
