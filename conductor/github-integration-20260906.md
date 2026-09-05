# GitHub integration closeout: 6 September 2026

Existing tracks: **T00**, **T06**, **T07**. This is a finite integration work
package, not a new track and not completion of all work in those tracks.

## Completed work package

The recovered code/history, NZ/ANZ integration, strict test toolchain, genuine
lock and lint/type/security repairs are merged into the canonical repository.
PR #8 was already merged when this closeout began. Its main-branch commit is
`f3ecbc3c40f6f1f6e458b04ec6bae7a6420cfa3c`, tree
`8e784a9183b93df26f9d5cc0f638af089772f908`, retaining PR head
`a25440943850ba0a7553a0487403c508afb1c011` as a parent.

The four post-merge push workflows all passed: Context CI 33970758018, Strict
Python Quality 33970758019, Test-Goblin 33970758030 and Security and Context
33970758051. Job-level inspection confirmed actual checker, full-test, package,
secret-scan, workflow-audit, CodeQL, locked-vulnerability-audit and SBOM execution.

Quality artifact 9970844996 was downloaded and SHA-256 verified against the Hub
metadata (GitHub Actions, not Hugging Face). Its receipt names the exact main
commit, Python 3.14.6 and the unchanged lock hash. JUnit reports 348 tests with
zero failures/errors/skips. Coverage is 97.30% combined, 98.19% statement-only and
93.86% branch-only; the required minimum remains 95% combined. No new test or
coverage claim is inferred from a previous branch run.

Machine-readable evidence: `quality/github-integration-main-20260906.json`.
The receipt pins its observed code head and does not claim to qualify its own
later commit. The documentation closeout receives normal PR and merge checks.

## Context reconciliation

The root deployment record, current implementation status, remaining-work page,
Conductor index and deterministic context manifest now distinguish completed
GitHub work from remaining data work. The prior import and strict-failure
checkpoints remain historical evidence. Do not reopen the completed integration
package simply because old documentation reported unresolved work.

No source code, test, dependency lock, strict setting, workflow, source collection,
framework registration or track state is changed by this documentation package.
The existing registry remains authoritative. Native external-tool qualification
still prevents a blanket claim that every foundation task is complete.

## Separate unfinished milestones

T02 owns live public HF publication, source-specific document acquisition,
coverage/disposition accounting and final Bronze closure/reconstruction. T03-T05
remain sequentially gated on that evidence and real parser/extraction/comparison
qualification. Registered authorities and profiles are not a complete corpus.

No HF writes, credential provisioning, live policy captures, paid compute,
mutation/prerelease experiments or medallion promotions are part of this closeout.
A green main branch establishes tested software, not validated policy advice or
a deployed public data product. See `docs/deployment/remaining-work.md`.
