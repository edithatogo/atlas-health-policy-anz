# Conductor

Conductor is the repository's authoritative context, requirements, planning and evidence system.

Each active track has:
- `spec.md` — problem, scope, requirements and non-compensatory gates;
- `plan.md` — implementation sequence and executable tasks;
- `metadata.toml` — status, dependencies, outputs and links;
- optional `decisions.md`, `evidence/`, and validation receipts.

The master registry is `conductor/registry.toml`. Completed tracks remain in place as part of project memory.

Execution models do not consume this context wholesale. For model-backed work, the deterministic orchestrator compiles the relevant Conductor/skill/evidence state into a bounded microtask packet under `.context/tiny-models.toml`. CI/context drift is governed by `.context/ci.toml` and `scripts/validate_context.py`.

## Recovery and deployment checkpoints

Read `docs/IMPLEMENTATION_STATUS.md`, `evidence/engineering/recovery-20260905/`, and `conductor/deployment-import-20260905.md` for the preserved recovery/import evidence. Source restoration and CI qualification do not close a production medallion layer. Later features named in historical chat summaries require code evidence; they must not be assumed present.

## Current ANZ expansion

Read [ANZ source and authority checkpoint](anz-scope-20260905.md) last. It supersedes older NZ-future-only roadmap wording and records the current source registration, coverage denominators, execution interfaces and CI evidence boundaries. No additional Conductor tracks are introduced.
