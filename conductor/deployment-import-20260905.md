# Hosted deployment checkpoint: 2026-09-05

This checkpoint belongs to existing track **T00** (foundation/deployment integration). It does not create a track, close T00 as a whole, or promote a medallion layer. T02 remains responsible for the unfinished public Bronze data product.

## Completed and verified remotely

- Pull request: https://github.com/edithatogo/atlas-health-policy-anz/pull/4
- PR branch: `fix/complete-atlas-import`; base: `main`.
- Repair commit: `02cad1fefcab74d129e5cd62482c48863cee4dd3`.
- Hosted recovery run: https://github.com/edithatogo/atlas-health-policy-anz/actions/runs/33958000207 (success).
- Restored import commit: `4ea9710c5eeb041a758415ccc67a6ef67710e2fd`.
- Exact recovered parent: `9cb1e709b8380dd71d35f22f866a02187119a3e2`.
- Exact recovered source tree: `a7211fdde23bafc254a10c52e755448b98665551`.
- All 252 original tracked files were checked against the source Git blob identity and file mode.
- The merge commit retains both the prior GitHub branch and recovered source commit as parents. No history rewrite or direct update to main occurred.
- The workflow passed transport rejection tests, immutable compressed/stream identity checks, Git reconstruction, source inventory verification, Python syntax compilation, Conductor/context reconciliation and the PR-branch push.
- Durable receipt: `.atlas-import/import-receipt.json` at the import commit.

The repaired manifest was computed from the verified archive, with the original whole compressed checksum unchanged. Both damaged tail chunks were replaced. Validation rejects extra/missing/reordered files, wrong sizes, altered hashes, symlinks, path traversal, duplicate JSON keys and attempts to restore onto main. Twelve focused checks and an idempotent clean-recovery integration test also passed locally.

## Qualification boundary

The hosted recovery ran with bootstrap Python **3.12.3**. Its syntax/context checks are not qualification of the declared Python 3.14.6 production runtime or a substitute for the full application test suite. The importer deliberately leaves `production_runtime_qualified` and `production_medallion_qualified` false. This documentation commit requests fresh PR checks on the now-restored tree; their actual results must be inspected before readiness is asserted.

## Remaining acceptance work

- Inspect and repair hosted application CI/dependency-contract failures; retain exact revisions and real lock/benchmark evidence.
- Keep PR #4 draft until import/application acceptance is established. Do not auto-merge.
- Configure a scoped HF write credential through the repository's secret mechanism and verify public dataset creation/uploads independently.
- Execute live source-adapter qualification and original-byte acquisition, then close Bronze v1 against its frozen scope and fixity/coverage contract.
- Progress through Silver, Gold and Platinum only after each upstream release and its method benchmarks qualify.

No original policy documents were captured and no HF repository writes were performed by this recovery run. The initial corpus remains Australian; no New Zealand coverage is implied. See `docs/deployment/remaining-work.md` for the baseline diagnosis and finite deployment criteria.
