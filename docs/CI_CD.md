# CI/CD and dependency policy

## Alignment with current archetypes
The repository follows the current common pattern in `archive-govt-nz` and `global-medicines-atlas`:
- CPython 3.14 with an exact canary runtime (`3.14.6` initially);
- `uv`-managed dependency groups and a mandatory lockfile once the first qualified installable production dependency/package is adopted;
- pinned GitHub Actions commit SHAs and `persist-credentials: false`;
- `ubuntu-24.04` standard runners by default;
- concurrency cancellation;
- Ruff + basedpyright/ty + pytest/Hypothesis;
- property/metamorphic/contract/edge tests and targeted mutation testing for critical logic;
- actionlint + zizmor for workflow security;
- Gitleaks for repository/history secret detection;
- pip-audit + CycloneDX SBOM;
- CodeQL;
- dependency-review on pull requests;
- Renovate inheriting `github>edithatogo/renovate-config`, with minimum release age and digest pinning.

## CI lanes
### Context
Runs on every pull request and main push. Validates Conductor, TOML manifests, tiny-model packet rules, track gates and workflow syntax/security.

### Core quality
Once executable code exists, split into smoke/unit/integration/property/metamorphic/contract/edge lanes. Heavy mutation/gremlin/profiling runs are change-scoped and/or scheduled rather than multiplied across every trivial documentation change.

### Security and supply chain
Runs on PR/main plus weekly schedule. Produces persistent receipts for leaks, SBOM and audit state. Release packages should receive GitHub artifact attestations so users can verify build provenance independently.

### Model/prompt qualification
Model calls are not required for routine code CI. CI uses deterministic fixtures and recorded responses for contracts. Live local/open-model benchmarks run on explicit benchmark workflows or free/available compute and publish a model/prompt manifest plus metrics rather than changing production routing directly.

## Free-resource strategy
Because the intended GitHub repository is public, standard GitHub-hosted runners are the default high-volume compute substrate. Large data are not uploaded as Actions artifacts; they live in versioned Hugging Face datasets/Xet. Actions artifacts normally retain only small receipts, reports and attestations with short retention. The bounded diagnostic-only exception below is not canonical data storage.

## Release publication
GitHub Actions builds release manifests and publication candidates; Hugging Face remains the data plane. Publication is followed by remote revision/hash/schema/viewer verification. A GitHub release receipt records the corresponding HF immutable revision.


## Current locked foundation and offline acquisition preflight
The production Python 3.14.6 lock and strict test/security environment are already
qualified; the earlier bootstrap-only description is historical. `uv.lock` is
required and normal jobs use locked synchronization, vulnerability auditing and
CycloneDX. Conductor and source-packet verification also retain dependency-free
exact-runtime lanes.

Relevant PRs compile an offline acquisition plan, checking exact policy identities,
unique source membership, matrix size and positive integer frontier budgets. The
scheduled Bronze workflow installs the exact interpreter BEFORE importing the
package, rather than relying on the runner default. No credential or capture job
is available to PR execution. The existing schedule and three-job concurrency are
unchanged. Plan and capture consume the same fixed collection and budget settings.

The default ANZ plan has 220 profiles and 20 frontier attempts per source. The
plan compiler caps aggregate frontier attempts at 5,120 and matrix jobs at 256.
These are programmatic limits, not a guarantee on redirects, HF transfers, billed
runtime or coverage. See `conductor/intake-compatibility-20260910.md`.

## Attestation and agentic automation boundaries
Use GitHub Artifact Attestations for release packages and SBOMs once there are release artefacts. GitHub Agentic Workflows may later augment issue/CI/docs maintenance, but they must not replace deterministic evidence qualification or medallion gates. GitHub Models is not part of the design; the service was retired in 2026, so model experimentation should use local/Hugging Face/provider-specific routes instead.

## Free-resource boundaries
Standard GitHub-hosted runners are the preferred free compute substrate while the repository is public. Store compact receipts/reports in Actions artifacts by default; durable datasets belong on Hugging Face. The small seed-probe exception below has explicit size and expiry limits. Hugging Face Dataset Viewer/Parquet/Croissant and Xet are useful public-data services. ZeroGPU can support bounded demos/spot evaluation within its quota. Hugging Face Jobs are pay-as-you-go and therefore are not assumed to be a free production dependency. Agentic Workflows similarly depend on a configured AI engine and are optional maintenance automation, not free deterministic compute.


## Bounded seed-access diagnostic exception

The trusted-main `seed-probe.yml` diagnostic may retain at most nine 2 MiB source-
stage bundles for seven days, with compact references, a pinned plan and access
dispositions. This permits access testing and independent replay without HF
credentials. It is not canonical corpus storage or a medallion release, and adds no
recurring schedule. PRs compile the offline plan only. Existing original-packet
and full-corpus workflows remain receipt-only. See `docs/CAPTURE_BUNDLES.md`.
