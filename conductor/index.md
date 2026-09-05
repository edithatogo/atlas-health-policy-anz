# Conductor

Conductor is the repository's authoritative context, requirements, planning and evidence system.

Each active track has:
- `spec.md` — problem, scope, requirements and non-compensatory gates;
- `plan.md` — implementation sequence and executable tasks;
- `metadata.toml` — status, dependencies, outputs and links;
- optional `decisions.md`, `evidence/`, and validation receipts.

The master registry is `conductor/registry.toml`. Completed tracks remain in place as part of project memory.


Execution models do not consume this context wholesale. For model-backed work, the deterministic orchestrator compiles the relevant Conductor/skill/evidence state into a bounded microtask packet under `.context/tiny-models.toml`. CI/context drift is governed by `.context/ci.toml` and `scripts/validate_context.py`.

## Current recovery checkpoint

Read `docs/IMPLEMENTATION_STATUS.md` and
`evidence/engineering/recovery-20260905/` before continuing. This pass recovered
`a15c911`, rebuilt operational staging and corrected institutional gap direction.
T00/T02/T07 remain active. No production layer was closed. No new tracks were
created. Later features named in earlier chat summaries require code evidence;
they must not be assumed present.
