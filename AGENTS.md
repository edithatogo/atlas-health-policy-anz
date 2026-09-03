# Agent Operating Contract

This repository uses Conductor as the authoritative context-management and work-planning system.

## Context load order
Read `.context/project.toml`, then every `required_context` entry in order before consequential changes.

## Work discipline
- Every substantive change must belong to a Conductor track.
- Track requirements, plans, decisions, evidence and validation receipts must remain mutually consistent.
- Respect the current medallion maturity gate: planning may look ahead, but production derivation may not bypass Bronze→Silver→Gold→Platinum qualification.
- Preserve source provenance and uncertainty; never infer absence from non-retrieval.
- Reuse before build. Consult `.context/ecosystem.toml` before creating overlapping functionality.
- SourceRight, CiteWeft and Authentext are mandatory quality-toolchain dependencies for source-bearing or publication-facing outputs.
- Do not use Git submodules for ecosystem dependencies; use thin adapters and exact-revision integration records.
- Semantic/vector/model outputs are derived evidence, never the canonical source of truth.
- Model consensus does not override failed source, rights, scope, authority, temporal or provenance gates.
- Human gates in `.context/project.toml` must not be auto-asserted as passed.

## Comparison discipline
- Qualify comparability before equivalence.
- Prefer deterministic and extractive methods before generative inference.
- Use method triangulation with orthogonal failure modes; use multi-model triangulation only when benchmark evidence justifies it.
- Every model-backed result records immutable model revision, prompt/schema, parameters, source hashes and abstention/disagreement state.
- Do not collapse distinct analytical frameworks into a single score unless commensurability is explicitly demonstrated.

## Git discipline
- Keep commits scoped and descriptive.
- Do not rewrite history after an evidence receipt references a commit.
- Validation receipts should identify the commit they validate.
