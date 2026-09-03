# Agent Operating Contract

This repository uses Conductor as the authoritative context-management and work-planning system.

## Context load order
Read `.context/project.toml`, then every `required_context` entry in order before consequential changes.

## Work discipline
- Every substantive implementation change must belong to a Conductor track. Roadmap-only experiments/features may be recorded without creating tracks.
- Track requirements, plans, decisions, evidence and validation receipts must remain mutually consistent.
- Respect the current medallion maturity gate: planning may look ahead, but production derivation may not bypass Source Census→Bronze→Silver→Gold→Platinum qualification. Close each finite release against `conductor/completion.md` rather than allowing optional refinement to keep it open.
- Preserve source provenance and uncertainty; never infer absence from non-retrieval.
- Reuse before build. Consult `.context/ecosystem.toml` before creating overlapping functionality.
- SourceRight, CiteWeft and Authentext are mandatory quality-toolchain dependencies for source-bearing or publication-facing outputs.
- Do not use Git submodules for ecosystem dependencies; use thin adapters and exact-revision integration records.
- Semantic/vector/model outputs are derived evidence, never the canonical source of truth.
- Model consensus does not override failed source, scope, authority, temporal, coverage or provenance gates.
- Operate autonomously according to `.context/autonomy.toml`: promote A0/A1, report A2/A3 with verification labels, and abstain A4. Human intervention is exception-only.

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
