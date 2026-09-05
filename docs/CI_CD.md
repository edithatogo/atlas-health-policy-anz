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
Because the intended GitHub repository is public, standard GitHub-hosted runners are the default high-volume compute substrate. Large data are not uploaded as Actions artifacts; they live in versioned Hugging Face datasets/Xet. Actions artifacts retain only small receipts, reports and attestations with short retention.

## Release publication
GitHub Actions builds release manifests and publication candidates; Hugging Face remains the data plane. Publication is followed by remote revision/hash/schema/viewer verification. A GitHub release receipt records the corresponding HF immutable revision.


## Foundation bootstrap state
The current repository is still context/schema infrastructure and has not adopted a qualified production Python package dependency set. Do not fabricate a lockfile in an environment that cannot resolve Python 3.14/dependencies. Current Actions run the standard-library context validator in an isolated exact 3.14.6 runtime. Once production dependencies are accepted, `uv.lock` becomes required and supply-chain CI switches to `uv sync --locked`, pip-audit and CycloneDX.

## Attestation and agentic automation boundaries
Use GitHub Artifact Attestations for release packages and SBOMs once there are release artefacts. GitHub Agentic Workflows may later augment issue/CI/docs maintenance, but they must not replace deterministic evidence qualification or medallion gates. GitHub Models is not part of the design; the service was retired in 2026, so model experimentation should use local/Hugging Face/provider-specific routes instead.

## Free-resource boundaries
Standard GitHub-hosted runners are the preferred free compute substrate while the repository is public. Store only compact receipts/reports in Actions artifacts; durable datasets belong on Hugging Face. Hugging Face Dataset Viewer/Parquet/Croissant and Xet are useful public-data services. ZeroGPU can support bounded demos/spot evaluation within its quota. Hugging Face Jobs are pay-as-you-go and therefore are not assumed to be a free production dependency. Agentic Workflows similarly depend on a configured AI engine and are optional maintenance automation, not free deterministic compute.
