# Strict-remediation checkpoint, 5 September 2026

Existing tracks: **T00** (quality integration), **T06** (comparison assurance),
**T07** (bounded workflows). No new tracks, release closure or medallion promotion.

The source base is `99140d55c9d570abdf746a7d1f8de07dd03e7133`, subsequently
merged through PR #7 at `5c16abba4db722d3e2228d4137c06f8ee730cf26`. The follow-up
branch is `fix/strict-type-quality`. ANZ/NZ registry and identity-sensitive coverage
contracts remain unchanged.

## Implemented

- Explicit validated object boundaries and typed serializers, CLI arguments,
  callbacks, optional SDK interfaces and mutable test fixtures.
- Complex acquisition, publication, comparison, graph and context-validation
  paths separated into bounded helpers, including initialized result handling.
- Empty-benchmark rejection and A2/A3 classification of unqualified local rule
  extraction, including derived graph properties.
- Strict JSON numeric/duplicate-key checks and HTTP/parser response validation.
- Local runtime proxy bypass, redirect refusal, endpoint and response budgets.
- Exact diagnostic remediation, API documentation, error classes, executable
  script modes and narrow justified boundary exceptions; no type-ignore additions.
- 69 regression cases in addition to all 279 retained cases.

## Local evidence

`quality/strict-remediation-local.json` records the exact restored CI runtime,
zero failures in all four strict checkers, 348 tests, and 97.19% combined coverage.
Those local results are retained separately from the hosted run below.

## Hosted repair qualification

Run: https://github.com/edithatogo/atlas-health-policy-anz/actions/runs/33970080952

The run passed all transport, inventory, strict-checker, serial coverage, parallel
repeat, benchmark, Conductor and whitespace checks before creating source commit
`0e0e821ba354ddbf10cb938a85b047fdde75fe3a`. All 104 reviewed changed paths were
verified against their exact Git object identities and file modes. The central
quality configuration and `uv.lock` retain their original hashes.

- Python 3.14.6 and the committed locked tools; no host-compatibility override.
- Ruff, Ruff format, basedpyright and ty: passed over src, scripts and tests.
- Tests: 348, with zero failures, errors or skips. Parallel execution repeats
  these tests and is not counted as another 348 unique cases.
- Hosted combined coverage: 97.30%; statement coverage: 98.19%; branch-only
  coverage: 93.86%. The unchanged gate is 95% combined coverage.
- Durable evidence: `quality/strict-remediation-hosted.json` and the run artifact.

The temporary write-enabled repair workflow and all transport files are removed
from the final working tree. They remain in Git history for audit, not execution.
The ordinary PR workflows must now independently validate the final PR head,
including complete-history Gitleaks, CodeQL, actionlint, zizmor, the locked
vulnerability audit and SBOM generation. A repair-run pass alone is not a claim
that those independent checks have passed.

Public HF deployment and sequential Bronze/Silver/Gold/Platinum completion remain
separate unfinished data-product milestones. No HF write or policy capture was
performed, no main branch was directly changed, and no automatic merge was enabled.
