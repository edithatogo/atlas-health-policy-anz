# System Requirements

## Architecture and provenance
- Federated architecture compatible with the maintainer's existing GitHub and Hugging Face ecosystem.
- `archive-govt-nz` is the acquisition/preservation archetype; `global-medicines-atlas` is the comparative-evidence archetype.
- Canonical medallion progression is Bronze -> Silver -> Gold -> Platinum, with non-compensatory maturity gates between layers.
- Bronze originals are immutable and never replaced by downstream derivatives.
- Gold assertions are bitemporal, provenance-bearing and source-span addressable.
- Every Platinum comparison is reconstructible from Gold plus pinned frameworks, code, parameters and model manifests.
- Every downstream layer is reconstructible from Bronze plus locked code/manifests.
- Initial implementation is divided into finite release contracts (census, Bronze, Silver, Gold, Platinum, gap-analysis engine) with explicit closure evidence.

## Public data plane
- All project medallion datasets are public Hugging Face datasets; no private Hugging Face dataset is part of the target architecture.
- The maintainer has authority to redistribute the source corpus. Redistribution is therefore not a routine approval gate.
- SourceRight is used for source identity, provenance/source-quality metadata and reproducible source handling; it must not generate repetitive publication-approval prompts.
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
- Confidence is claim-level and derived from evidence dimensions, not model self-reported confidence.
- A report may autonomously include provisional findings when their verification requirement is explicit.

## Autonomy
- Routine acquisition, medallion promotion, public Hugging Face publication, comparison, framework analysis, gap analysis and living updates are autonomous when machine gates pass.
- Programmatically verified evidence and robust method/model triangulation support full autonomous assertion.
- Incomplete or conflicting evidence does not stop the overall workflow: the affected finding is downgraded to an explicit A2/A3 state or A4 abstention.
- Human intervention is exception-only: unavailable credentials, destructive/irreversible external mutations, or explicitly requested manual adjudication.
- The system must not generate repetitive approval requests for routine reversible work.

## Quality and governance
- Deterministic context loading and Conductor reconciliation.
- Reuse-before-build ecosystem governance.
- SourceRight, CiteWeft and Authentext integrated as mandatory governed dependencies.
- Git-tracked changes and evidence receipts.
- Fail-closed handling of missing, conflicting or unqualified evidence at the *claim promotion* boundary; uncertainty is reported rather than silently discarded.
- Benchmark-driven adoption of parsers, retrieval models, embeddings, NLI/cross-encoders and generative models.
- Discrete completion receipts prevent endless refinement from blocking agreed release scope.

## Tiny/local-model execution
- Program code owns state, method selection, routing, retry/escalation, medallion transitions and stop conditions.
- Model execution consumes a versioned single-question microtask packet with exact evidence spans, invariants, output schema and enumerated abstention codes.
- Canonical model outputs require constrained decoding and deterministic schema/span/hash verification.
- Context budgets and retry/escalation counts are finite and machine-enforced.
- Model/task qualification is per task class; no parameter-count or brand is globally authoritative.
- The system supports network-denied local execution and must not require private institutional text, embeddings, prompts, traces or results to leave the deployment.

## CI/CD and supply chain
- Current baseline aligns to the maintainer ecosystem: exact Python 3.14.6, uv 0.11.29, SHA-pinned GitHub Actions, least privileges and disabled persisted checkout credentials.
- Public GitHub standard runners are preferred for routine deterministic CI; heavy model inference is not a routine CI requirement.
- Dependency review, CodeQL, Gitleaks, actionlint/zizmor, pip-audit, CycloneDX and Renovate are required when applicable.
- Once a qualified installable production dependency set exists, `uv.lock` is mandatory and CI uses `uv sync --locked`.
- Critical promotion/lineage/comparison logic targets 100% line/branch coverage plus mutation/property/metamorphic tests; overall production coverage is at least 95%.
