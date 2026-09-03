# T00 — Foundation and Context Management

## Objective
Establish deterministic Conductor context management, Git traceability, archetype inheritance and governed SourceRight/CiteWeft/Authentext dependencies.

## Requirements
- Context spine and deterministic load order exist.
- Conductor master documents and registry exist.
- Reuse registry names `archive-govt-nz` and `global-medicines-atlas` as archetypes.
- SourceRight, CiteWeft and Authentext are mandatory governed dependencies.
- No Git submodules.
- Compatibility fallback cannot masquerade as native provider execution.
- Context and dependency drift must be machine-detectable.

## Non-compensatory gates
- Required context file missing -> fail.
- Track missing spec/plan/metadata -> fail.
- Required dependency omitted from manifests -> fail.
- Human gate auto-asserted -> fail.
