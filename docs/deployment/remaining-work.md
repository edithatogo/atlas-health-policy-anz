# Remaining Atlas deployment work

Canonical repository: `edithatogo/atlas-health-policy-anz`.

## Observed baseline

On 2026-09-05, `main` at `60a44d4e0edead7a51c47dd819997b86f1f99bd9` contained import transports, GitHub workflows and `DEPLOYMENT.md`, but not the application source, tests or Conductor context. The earlier import pull requests were merged; merging their transport files did not restore the application. The latest observed main-branch Context CI and Test-Goblin runs failed.

The intact delivery archive remains available with SHA-256 `fa1045fe6aafa0e4b84c9227c1be9dfc54c49241c8ea1250386c2e2e892c4542`, size 889683 bytes and 845 members. It contains source commit `9cb1e709b8380dd71d35f22f866a02187119a3e2`, tree `a7211fdde23bafc254a10c52e755448b98665551`, and 252 tracked files.

A fresh `git fast-export --all` and XZ preset-9 compression reproduce the transport's existing whole-payload SHA-256 `04ff28fd3fd6e24e1229d1892576ba0719a0ff2f343b6da5d27bf5e07894f792`. The first 29 encoded chunks match their remote Git blob identities. Chunks 030 and 031, the per-part manifest hashes and the uncompressed stream hash require correction from the verified archive, not relaxation of integrity checks.

## This pull request: import recovery

- Repair the two damaged chunks and regenerate the manifest from the verified archive.
- Validate every chunk, the compressed payload, the bounded decompressed stream, the reconstructed commit, the complete source tree and all 252 tracked files.
- Preserve both existing repository history and recovered source history in a non-rewriting import on this PR branch.
- Refuse any attempt to push directly to `main`, force-push, or change workflows from the recovery job.
- Record a machine-readable import receipt; do not confuse import verification with production qualification.
- Re-run application/context checks on the fully restored branch and retain any failures honestly.

## Subsequent finite milestones (not claimed complete)

1. Qualify hosted CI and the committed Python/dependency contracts; generate a genuine dependency lock in a networked environment. Do not weaken versions or gates merely to make bootstrap checks green.
2. Configure a scoped Hugging Face write credential through repository secrets, never in code, PR text or chat. Verify public dataset creation and exact-revision anonymous downloads. Read-only connector access is not write permission.
3. Execute and qualify the Australian source adapters. A 28-surface inventory or an exhausted bounded crawl is not an exhaustive document census.
4. Close public Bronze v1 only with verified original bytes, capture receipts, declared scope/dispositions and remote fixity verification. Never promote fixtures or shadow material.
5. Progress sequentially through qualified Silver v1, Gold v1 and Platinum v1, retaining parsing, extraction and comparison benchmark gates, uncertainty and provenance.

These are acceptance criteria for the existing work, not new Conductor tracks. Australia remains the first corpus; the ANZ repository name does not imply New Zealand coverage. No Hugging Face write, corpus acquisition or production medallion promotion is implied by this PR.
