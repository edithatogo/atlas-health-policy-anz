# Design

## Architectural inheritance
- `archive-govt-nz`: acquisition, preservation, fixity, provenance, medallion and evidence-gating patterns.
- `global-medicines-atlas`: bitemporal canonical evidence, cross-jurisdiction comparison, explicit uncertainty and validity, DuckDB/Parquet analytical plane.

## Context architecture
`.context/project.toml` defines deterministic context and required manifests. `.context/ecosystem.toml` governs reuse. `.context/dependencies.toml` governs external quality-toolchain dependencies. Conductor tracks define executable project memory.

## Quality toolchain
SourceRight -> source rights/quality and claim-evidence integrity.
CiteWeft -> citation extraction/linkage/reference integrity.
Authentext -> humanization/readability/style assessment.
All integrations use thin adapters and exact-revision records when native dependencies are available; compatibility mode must be explicit when not.
