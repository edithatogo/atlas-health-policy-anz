# Conductor

Conductor is the repository's authoritative context, requirements, planning and evidence system.

Each active track has:
- `spec.md` - problem, scope, requirements and non-compensatory gates;
- `plan.md` - implementation sequence and executable tasks;
- `metadata.toml` - status, dependencies, outputs and links;
- optional `decisions.md`, `evidence/`, and validation receipts.

The master registry is `conductor/registry.toml`. Completed tracks remain in place as part of project memory.

Execution models do not consume this context wholesale. For model-backed work, the deterministic orchestrator compiles the relevant Conductor/skill/evidence state into a bounded microtask packet under `.context/tiny-models.toml`. CI/context drift is governed by `.context/ci.toml` and `scripts/validate_context.py`.

## Current GitHub integration and qualification

Read [GitHub integration closeout](github-integration-20260906.md) after the dated
import, ANZ and strict-quality checkpoints. PR #8 is merged. All four ordinary
post-merge workflows passed at `f3ecbc3c40f6f1f6e458b04ec6bae7a6420cfa3c`.
`quality/github-integration-main-20260906.json` records the exact runs, verified
artifact, tests and coverage. Older statements that import, dependency locking or
strict lint/type remediation are pending are superseded, not silently erased.
The closeout is a completed integration work package within T00/T06/T07; it does
not close those entire tracks or promote a production medallion release.

## Recovery and deployment checkpoints

Read `docs/IMPLEMENTATION_STATUS.md`, `evidence/engineering/recovery-20260905/`, and `conductor/deployment-import-20260905.md` for preserved recovery/import evidence. Source restoration and CI qualification do not close a production medallion layer. Later features named in historical chat summaries require code evidence; they must not be assumed present.

## ANZ expansion

Read [ANZ source and authority checkpoint](anz-scope-20260905.md). It supersedes older NZ-future-only roadmap wording and records source registration, coverage denominators, execution interfaces and evidence boundaries. No additional Conductor tracks are introduced.

## Strict-quality history and current execution

[strict-quality-20260905.md](strict-quality-20260905.md) and
[strict-quality-results-20260905.md](strict-quality-results-20260905.md) describe
the introduction of stricter gates. The failures recorded there were subsequently
repaired; see [strict-remediation-20260905.md](strict-remediation-20260905.md) and
the current closeout, rather than treating those historical diagnostics as open.

The strict-toolchain lock was resolved and installed on hosted Python 3.14.6 in run `33961762760`, with source commit `6a3e5abb71a3b63bd17bb90aeb175edc7e57d2f3`. Exact selected tools and hashes remain in `quality/resolved-test-tools.json` and `uv.lock`. The later post-merge runs supply runtime, test and security qualification; resolution alone was not sufficient.

Use `uv run --no-sync python scripts/test_goblin.py routine` after synchronizing the declared locked test environment. Direct unconfigured pytest calls do not autoload arbitrary installed plugins. Canonical qualification uses the complete coverage profile; changed-test selection is never a release gate.
