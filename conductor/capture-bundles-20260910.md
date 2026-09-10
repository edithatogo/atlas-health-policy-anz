# Capture bundles: 10 September 2026 (Australia/Brisbane)

Existing **T02/T07** finite work package. No new track or production promotion.
This continues PR #15's acquisition preflight at main
`30ebb9bc0add05042839eb8ef214d1492d208368`. That implementation remains intact.

## Implemented interfaces

- `capture_bundle.py`: deterministic, bounded transport of existing verified source
  stages and independent replay requiring both reference and governed policy pins.
- `seed_probe.py`: exact nine-jurisdiction seed access plan and a credential-free
  diagnostic with distinct probe identities and retained capture/failure states.
- `seed-probe.yml`: secret-free PR planning and trusted-main-only live diagnostics.
- `docs/CAPTURE_BUNDLES.md`: limits, trust model, commands and completion boundary.

The ordinary source stage and HubStore are reused. Raw bytes are never interpreted
as instructions. Control flow, validation, execution limits and confidence are
programmatic, not delegated to tiny models. No new library or model is required.

The diagnostic makes acquisition access observable while HF publication credentials
are unavailable. Nine 2 MiB maximum replay bundles may be retained for seven days
as an explicit diagnostic-only Actions artifact exception; they are not a durable
public corpus or substitution for HF. No new recurring job is introduced.

## Acceptance

The exact locked Python 3.14.6 runtime was reconstructed from checksum-verified
Actions artifacts for local testing. The source snapshot identifies `c20358e8`,
whose only addition to main was the temporary development-export workflow. That
workflow is removed from the final tree. The local baseline Git commit is synthetic
and is never represented as the remote tested source identity.

Run all strict tools, the complete coverage suite, independent parallel execution,
benchmarks and Conductor reconciliation before submitting. The initial 41 new
regression cases cover independent pins, archive mutations, unsafe members, budgets,
policy drift, selection identity, failed access, interrupted journals and replay.
Exact local measurements are in `quality/capture-bundles-local-20260910.json`.
Hosted PR acceptance and actual live capture results must be observed separately;
local passing tests do not establish either. Record final remote results in the PR,
not a self-certifying code receipt.

## Unchanged state

Original PDFs/intakes, source and authority registries, `pyproject.toml`, `uv.lock`
and strict/coverage gates are unchanged. The existing T02 unresolved work still
includes source-specific discovery, HF publication and final Bronze closure.
Native ecosystem-tool and parser/comparison qualifications remain separate. The
probe's depth-zero exhaustion is not a completed source census. No corpus coverage,
policy absence, HF write or later medallion release is implied by a passing job.

The concurrent credentialing/SoCP collection at
`c7fd8b8835034280badde76cfd8765b018c9abd5` is preserved unchanged in the combined
branch. Its additional tests and workflow are subject to hosted combined validation;
they were not part of the earlier 575-test local snapshot.
