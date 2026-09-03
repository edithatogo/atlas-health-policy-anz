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

    registry = load_toml(ROOT / "conductor/registry.toml")
    for track in registry.get("track", []):
        base = ROOT / track["path"]
        for name in ("spec.md", "plan.md", "metadata.toml"):
            if not (base / name).exists():
                errors.append(f"track {track['id']} missing {name}")

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print("OK context and Conductor reconciliation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
