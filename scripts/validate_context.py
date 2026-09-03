from __future__ import annotations

from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def load_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


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

    deps = load_toml(ROOT / ".context/dependencies.toml")
    ids = {d.get("id") for d in deps.get("dependency", [])}
    for required in {"sourceright", "citeweft", "authentext"}:
        if required not in ids:
            errors.append(f"missing required dependency: {required}")

    autonomy = load_toml(ROOT / ".context/autonomy.toml")
    levels = {level.get("id") for level in autonomy.get("level", [])}
    if levels != {"A0", "A1", "A2", "A3", "A4"}:
        errors.append("autonomy manifest must define exactly A0-A4")
    if not autonomy.get("principles", {}).get("minimal_approval_spam", False):
        errors.append("autonomy manifest must enforce minimal approval spam")
    forbidden_routine_gates = {"licensing", "public-release", "consequential-interpretation", "policy-recommendation"}
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
        for dep in track.get("depends_on", []):
            if dep not in track_ids:
                errors.append(f"track {track['id']} has unknown dependency: {dep}")

    # Production maturity is sequential. A downstream medallion track may be planned,
    # but it must not be marked active/completed before its predecessor is completed.
    sequence = [("T02", "T03"), ("T03", "T04"), ("T04", "T05")]
    started = {"active", "completed"}
    for upstream, downstream in sequence:
        if track_status.get(downstream) in started and track_status.get(upstream) != "completed":
            errors.append(
                f"medallion gate violation: {downstream} started before {upstream} completed"
            )

    if not (ROOT / "conductor/completion.md").exists():
        errors.append("missing discrete completion contract")

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print("OK context, autonomy and Conductor reconciliation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
