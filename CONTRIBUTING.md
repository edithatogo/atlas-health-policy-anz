# Contributing to atlas-health-policy-anz

Health Policy Atlas ANZ develops evidence-first comparison of Australian and New Zealand health policies and their authority context. Contributions should improve source fidelity, bounded acquisition, comparisons, diagnostics and reproducible verification.

## Before you start

Read [AGENTS.md](AGENTS.md), [.context/project.toml](.context/project.toml) and its required context in order, then the existing Conductor task. Review [implementation status](docs/IMPLEMENTATION_STATUS.md) and current pull requests. Preserve source-census and medallion qualification gates, separate issuing bodies and source provenance; incomplete retrieval does not establish absence.

For bugs, provide the affected version or commit, environment, minimal reproduction, expected result and observed result. For a substantial proposal, describe the use case and compatibility impact before expanding implementation scope. Use existing issue templates when offered.

## Development and validation

Use the locked runtime and dependencies specified by [Test-Goblin](.github/workflows/test-goblin.yml). Its existing test setup is:

```sh
uv sync --python 3.14.6 --group test-goblin --group publication --extra nlp --locked
uv run --no-sync python scripts/test_goblin.py unit
```

Select the relevant integration, smoke, property, contract or parallel lane for the change and retain the complete coverage/package gates at integration. The workflow defines the additional environment needed by those gates. Do not substitute a host-only runtime and then claim production-runtime qualification.

Add independent expected results for changed source, temporal, authority or comparison semantics. Qualify comparability before equivalence and retain uncertainty and abstention. Sensitive/local execution remains network-denied by default. Model output and graph projections are derived evidence, not canonical documents. A software fixture, staged source packet or successful upload does not close production corpus or legal-applicability gates.

## Pull requests

Create a focused branch from the current `main` branch and submit a pull request to this repository. Link the relevant issue or existing project task, explain the resulting behaviour, and update affected examples and documentation. Keep unrelated changes in separate pull requests.

Report executed commands, outcomes and the commit they validate. Identify unavailable checks and remaining limitations explicitly. Follow the repository's existing review and automated-check requirements; retain required gates and current ownership. Address findings and verify the final head before integration. Release and operational work follow the repository's existing autonomous, evidence-gated workflows within their authorised scope.

## Security, rights and conduct

Follow the [security policy](https://github.com/edithatogo/.github/blob/main/SECURITY.md). Use private vulnerability reporting if available; otherwise request a private contact without publishing vulnerability details. Keep credentials, personal information and restricted source material out of issues, fixtures, logs and artifacts.

Preserve existing attribution and third-party terms. This guide does not grant a licence; clarify any unclear redistribution rights before contributing external material. Follow the [code of conduct](https://github.com/edithatogo/.github/blob/main/CODE_OF_CONDUCT.md) and keep technical discussions respectful.

## Basis for this guide

This guide follows [GitHub's contribution-guideline guidance](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors) and the contribution-process and testing principles in [OpenSSF Best Practices](https://www.bestpractices.dev/en/criteria). It does not assert certification.
