# Atlas Health Policy ANZ: deployment record

## Current GitHub integration

Verified on 6 September 2026 (Australia/Brisbane). The canonical repository is
`edithatogo/atlas-health-policy-anz`.

PRs #4 through #8 have delivered the recovered application/history, CI repair,
resolved dependency lock, NZ/ANZ source integration, expanded test tooling and
strict-quality remediation. PR #8 is merged, not awaiting review. The verified
post-merge code revision is `f3ecbc3c40f6f1f6e458b04ec6bae7a6420cfa3c`.

All four push-triggered workflows passed at that revision:

| Workflow | Successful run |
|---|---:|
| Context CI | 33970758018 |
| Strict Python Quality | 33970758019 |
| Test-Goblin | 33970758030 |
| Security and Context | 33970758051 |

Job-level inspection confirmed that the strict checkers, full tests, dependency
audit, security checks and package build executed successfully. The downloaded
`atlas-quality-receipts` artifact was verified against its GitHub SHA-256 digest;
it records 348 tests with zero failures, errors or skips, and 97.30% combined
statement/branch coverage. Dependency review and Testing Frontier are separate
PR/event-triggered checks; their PR passes are not additional push runs.

See `quality/github-integration-main-20260906.json` for immutable identifiers,
exact measurements and qualification limits, and
`conductor/github-integration-20260906.md` for the current handoff.
This record qualifies the named code revision, not its own later documentation
commit. Every subsequent PR and merge must pass its own applicable checks.

## Source and history

The original recovery imported commit
`9cb1e709b8380dd71d35f22f866a02187119a3e2`, source tree
`a7211fdde23bafc254a10c52e755448b98665551`, and all 252 original tracked files.
Both recovered and existing GitHub histories were preserved. Historical import
failures remain recorded in `.atlas-import/import-receipt.json` and the dated
recovery checkpoints; they are not current deployment blockers.

## Scope and publication boundary

NZ is implemented as a jurisdiction and source/authority selection, not merely
reserved in the repository name. The governed catalogue contains 212
bodies/functions and 220 combined `anz-v1` acquisition profiles. The original
28-profile `au-v1` collection remains frozen and selectable. Directory membership
and configured sources are not evidence of a complete document corpus. See
`conductor/anz-scope-20260905.md` for exact denominators and remaining categories.

The public `edithatogo/au-health-policy-atlas-{bronze,silver,gold,platinum}`
dataset names are retained for compatibility. This GitHub closeout does not
create, inspect or publish those datasets, provision credentials, capture policy
documents or promote a medallion release. HF publication requires independently
verified write access and exact-revision byte verification.

## Remaining data-product work

Native ecosystem-tool qualification, real source acquisition, final Bronze
closure and empirical Silver/Gold/Platinum qualification remain open under the
existing Conductor tracks. The completed GitHub import, dependency lock and
strict CI repairs must not be repeatedly listed as unfinished work. See
`docs/deployment/remaining-work.md` for the separate acceptance criteria.
