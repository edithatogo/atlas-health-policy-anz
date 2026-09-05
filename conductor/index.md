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

Read [ANZ source and authority checkpoint](anz-scope-20260905.md). It supersedes older NZ-future-only roadmap wording and records the current source registration, coverage denominators, execution interfaces and CI evidence boundaries. No additional Conductor tracks are introduced.

## Current strict-quality work

Read [strict testing and static-analysis checkpoint](strict-quality-20260905.md) last. Existing T00/T06/T07 govern this work. The previous ANZ qualification does not cover the newly enforced Ruff/basedpyright/ty gates or new pytest profiles.

The strict-toolchain lock was resolved and installed on hosted Python 3.14.6 in run `33961762760`, with immutable source commit `6a3e5abb71a3b63bd17bb90aeb175edc7e57d2f3`. See `quality/resolved-test-tools.json` and `uv.lock` at commit `6449a3b7b70820f6bb79907581785546b7618041` for exact selected versions and hashes. Resolution is not test qualification; inspect the actual new-head workflow receipts.

Use `uv run --no-sync python scripts/test_goblin.py routine` after synchronizing the declared locked test environment. Direct unconfigured pytest calls no longer autoload arbitrary installed plugins. Canonical qualification uses the complete coverage profile; changed-test selection is never a release gate.
