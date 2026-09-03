# Design

## Architectural inheritance
- `archive-govt-nz`: source registries, bounded capture, content-addressed storage, WARC/WACZ where applicable, fixity, provenance, rights receipts, evidence gating, deterministic replay, maturity separation and public publication verification.
- `global-medicines-atlas`: source-specific adapters, canonical bitemporal evidence, explicit evidence states, DuckDB/Parquet analytical plane, uncertainty/coverage reporting, comparison validity, optional non-authoritative semantic layer, CLI/API/Atlas boundaries.

## Control plane and public data plane
**GitHub** holds code, Conductor, schemas, source registries, framework definitions, tests, workflows, publication manifests and evidence receipts.

**Hugging Face** holds rights-qualified public medallion datasets, public benchmarks, model evaluation artefacts and eventually a public Atlas/Space if justified. GitHub Actions or an equivalent governed publisher is the durable publication path; Hugging Face is never the ingest origin.

Proposed public dataset family:
- `edithatogo/au-health-policy-atlas-bronze`
- `edithatogo/au-health-policy-atlas-silver`
- `edithatogo/au-health-policy-atlas-gold`
- `edithatogo/au-health-policy-atlas-platinum`

Names are roadmap targets, not claims that the repositories currently exist.

## Medallion semantics
### Bronze
Original bytes/HTTP evidence, WARC/WACZ where suitable, rendered web snapshots when justified, capture receipts, rights state, fixity, URL, observation time, authority metadata and source census disposition. Bronze is lossless with respect to the declared capture contract.

### Silver
Document-level normalisation only: extracted text, layout/sections, tables, headings, page/DOM anchors, reference lists and typed metadata. Silver must preserve reversible lineage to Bronze spans/pages/nodes and explicit extraction losses.

### Gold
Atomic policy assertions and concepts. Typical assertion fields include actor, modality, action, object, trigger, timeframe, exceptions, setting, authority, bindingness, valid time, observation time, source span and uncertainty/evidence state. Gold also carries concept mappings and framework-addressable entities, but not unqualified cross-jurisdiction equivalence.

### Platinum
Only qualified comparisons: equivalence classes, contradictions, gaps, consensus/outliers, framework concordance, burden/complexity, governance architecture, temporal change and policy-frontier products. Each record carries comparison-validity state, methods/models used, coverage and provenance.

## Context architecture
`.context/project.toml` defines deterministic context and required manifests. `.context/ecosystem.toml` governs reuse. `.context/dependencies.toml` governs quality-toolchain dependencies. `.context/comparison.toml` governs comparison assurance. `.context/frameworks.toml` defines analytical framework classes. Conductor tracks define executable project memory.

## Quality toolchain
- **SourceRight**: source rights, source quality, redistribution qualification and claim-evidence integrity.
- **CiteWeft**: citation/reference extraction, source linkage and citation integrity.
- **Authentext**: humanization/readability/style quality of publication-facing narrative only; it does not modify canonical evidence records.

All integrations use thin adapters and exact-revision records when native dependencies are available; compatibility mode must be explicit when not.
