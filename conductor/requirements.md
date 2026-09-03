# System Requirements

## Architecture and provenance
- Federated architecture compatible with the maintainer's existing GitHub and Hugging Face ecosystem.
- `archive-govt-nz` is the acquisition/preservation archetype; `global-medicines-atlas` is the comparative-evidence archetype.
- Canonical medallion progression is Bronze -> Silver -> Gold -> Platinum, with non-compensatory maturity gates between layers.
- Bronze originals are immutable and never replaced by downstream derivatives.
- Gold assertions are bitemporal, provenance-bearing and source-span addressable.
- Every Platinum comparison is reconstructible from Gold plus pinned frameworks, code, parameters and model manifests.
- Every downstream layer is reconstructible from Bronze plus locked code/manifests.

## Public data plane
- All project datasets are intended to be public Hugging Face datasets; no private Hugging Face dataset is part of the target architecture.
- Public accessibility does not by itself establish redistribution rights. Raw source publication requires a positive SourceRight/right-to-redistribute decision; otherwise the capture may be retained locally with a public metadata/fixity/URL record until rights are resolved.
- GitHub remains the control/code/context plane. Hugging Face is the public dataset/benchmark/publication plane and is not the ingest origin.
- Remote publication claims require checksum/revision verification after upload.

## Comparative epistemics
- Comparison begins with comparability qualification, not normative ranking.
- Text similarity is not policy equivalence.
- Non-retrieval is not evidence of absence.
- A guideline is not a mandatory policy merely because terminology overlaps.
- A cited framework is not evidence of conformance with that framework.
- Consensus across jurisdictions is not evidence that a proposition is clinically correct.
- Model agreement is not ground truth.
- High-consequence comparative claims require exact source spans, authority/scope/temporal qualification and explicit uncertainty.

## Quality and governance
- Deterministic context loading and Conductor reconciliation.
- Reuse-before-build ecosystem governance.
- SourceRight, CiteWeft and Authentext integrated as mandatory governed dependencies.
- Git-tracked changes and evidence receipts.
- Fail-closed handling of missing, conflicting or unqualified evidence.
- Benchmark-driven adoption of parsers, retrieval models, embeddings, NLI/cross-encoders and generative models.
- Human gates remain for licensing, public release, consequential interpretation and final policy recommendation.
