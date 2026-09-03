# Design

## Architectural inheritance
- `archive-govt-nz`: source registries, bounded capture, content-addressed storage, WARC/WACZ where applicable, fixity, provenance, evidence gating, deterministic replay, maturity separation and public publication verification.
- `global-medicines-atlas`: source-specific adapters, canonical bitemporal evidence, explicit evidence states, DuckDB/Parquet analytical plane, uncertainty/coverage reporting, comparison validity, optional non-authoritative semantic layer, CLI/API/Atlas boundaries.

## Control plane and public data plane
**GitHub** holds code, Conductor, schemas, source registries, framework definitions, tests, workflows, publication manifests and evidence receipts.

**Hugging Face** holds public medallion datasets, public benchmarks, model evaluation artefacts and eventually a public Atlas/Space if justified. GitHub Actions or an equivalent governed publisher is the durable publication path; Hugging Face is never the ingest origin.

The maintainer has authority to redistribute the source corpus. Routine redistribution/publication is therefore autonomous once technical integrity gates pass.

Proposed public dataset family:
- `edithatogo/au-health-policy-atlas-bronze`
- `edithatogo/au-health-policy-atlas-silver`
- `edithatogo/au-health-policy-atlas-gold`
- `edithatogo/au-health-policy-atlas-platinum`

Names are roadmap targets, not claims that the repositories currently exist.

## Medallion semantics
### Bronze
Original bytes/HTTP evidence, WARC/WACZ where suitable, rendered web snapshots when justified, capture receipts, fixity, URL, observation time, authority metadata and source census disposition. Bronze is lossless with respect to the declared capture contract.

### Silver
Document-level normalisation only: extracted text, layout/sections, tables, headings, page/DOM anchors, reference lists and typed metadata. Silver must preserve reversible lineage to Bronze spans/pages/nodes and explicit extraction losses.

### Gold
Atomic policy assertions and concepts. Typical assertion fields include actor, modality, action, object, trigger, timeframe, exceptions, setting, authority, bindingness, valid time, observation time, source span and uncertainty/evidence state. Gold also carries concept mappings and framework-addressable entities, but not unqualified cross-jurisdiction equivalence.

### Platinum
Only qualified comparisons: equivalence classes, contradictions, gaps, consensus/outliers, framework concordance, burden/complexity, governance architecture, temporal change and policy-frontier products. Each record carries comparison-validity state, methods/models used, coverage, provenance and A0–A4 autonomy/evidence state.

## Discrete release architecture
The medallion is implemented as finite releases, not endless work streams. Source Census v1, Bronze v1, Silver v1, Gold v1 and Platinum v1 each have a frozen scope, candidate state, qualification gate, completion receipt and immutable manifest. Later discoveries create incremental releases.

## Comparison graph principles
- Canonical equivalence evidence is pairwise. `A≈B` and `B≈C` do not automatically imply `A≈C`.
- Equivalence classes are derived views over qualified pairwise relations and must expose any inconsistent triangle.
- Coverage is denominator-aware: every percentage states what source universe, document set or assertion set forms the denominator.
- Descriptive findings (what policies say/differ on) are separate from normative conclusions (what should be done).
- Claim-level confidence is evidence-derived and can vary within one report.

## Context architecture
`.context/project.toml` defines deterministic context and required manifests. `.context/ecosystem.toml` governs reuse. `.context/dependencies.toml` governs quality-toolchain dependencies. `.context/comparison.toml` governs comparison assurance. `.context/autonomy.toml` governs claim-level confidence/autonomy. `.context/frameworks.toml` defines analytical framework classes. Conductor tracks define executable project memory.

## Quality toolchain
- **SourceRight**: source identity, source quality/provenance and reproducible acquisition metadata. Redistribution is authorised for this project and is not a repetitive approval gate.
- **CiteWeft**: citation/reference extraction, source linkage and citation integrity.
- **Authentext**: humanization/readability/style quality of publication-facing narrative only; it does not modify canonical evidence records.

All integrations use thin adapters and exact-revision records when native dependencies are available; compatibility mode must be explicit when not.
