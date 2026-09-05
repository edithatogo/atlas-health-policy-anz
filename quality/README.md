# Testing and strict-quality evidence

The installed toolchain is pinned by `uv.lock`. `resolved-test-tools.json` records the actual Python 3.14.6 resolution, not merely version minima. `normalization-result.json` records the tested repairs and the remaining static-analysis findings; it is **not a suppression baseline** and cannot make a failing check pass.

## Reproduce from a clean checkout

```sh
uv python install 3.14.6
uv sync --python 3.14.6 --all-groups --all-extras --locked
uv run --no-sync python scripts/test_goblin.py coverage
uv run --no-sync python scripts/test_goblin.py parallel
uv run --no-sync python scripts/test_goblin.py benchmark
uv run --no-sync python scripts/strict_quality.py ruff
uv run --no-sync python scripts/strict_quality.py format
uv run --no-sync python scripts/strict_quality.py basedpyright
uv run --no-sync python scripts/strict_quality.py ty
```

Each pytest command loads only its allowlisted installed plugin entry points, disables Python sockets by default, sets deterministic seeds and retains a JUnit result and JSON receipt. Loopback HTTP is permitted only in the explicitly marked fixture test. Subprocess mocking is selective: the complete offline CLI and package smoke tests still exercise real local subprocesses. This is not an OS sandbox, and sensitive institutional workloads still require deployment-level egress controls.

Snapshot assertions remain active, but the governed runner never updates snapshots, locally or in CI. Performance tests retain correctness assertions without asserting a machine-independent latency threshold. The generated property suite is not counted as external clinical/model validation.

Changed-test selection (`pytest-picked`, `pytest-testmon`) is installed for development but never substitutes for the complete release suite. `pytest-gremlins` and `mutmut` are targeted mutation tools; the scheduled/manual gremlins experiment does not automatically pardon surviving mutants. Prerelease compatibility resolves a disposable lock in a read-only job and cannot publish or replace the qualified lock.

## Observed checkpoint

Hosted normalization run `33962142453` reconstructed the exact locked environment, repaired HTTPError response leaks, mapped zipapp subprocess coverage back to real source files, applied safe Ruff fixes and formatting, and passed **279 serial tests, 279 two-worker tests, one benchmark, Conductor validation and package build**. Source commit after normalization: `cd4d184d80ca721feb3c97bfa2c0893fab2d370b`.

Combined statement/branch coverage: **97.63%**; statement-only: **98.66%**; branch-only: **94.46%**. The existing 95% combined gate was unchanged. No source files were excluded to remove the zipapp warnings; coverage path aliases merge observations of identical code.

At that checkpoint, Ruff reported **1102 diagnostics**, basedpyright **1585 errors**, and ty **107 diagnostics**. Formatting passed. Those findings include pre-existing code and must be resolved through real annotations, validated typed data boundaries, smaller functions and explicit adapter contracts, not blanket ignores, fabricated casts, or lowering strictness. Current-head counts may change as repairs are committed; always consult that head's receipts.

The one-off write-enabled lock/normalization workflows are removed after their completed work. Routine tests, linting, typing and frontier experiments remain read-only. Nothing in this checkpoint qualifies source capture, public HF publication or a production medallion release.
