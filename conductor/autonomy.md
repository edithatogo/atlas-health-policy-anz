# Autonomy and Confidence-Gated Operation

The project is designed to run autonomously by default. Human approval is an exception path, not a routine workflow stage.

## Operating rule
Routine source acquisition, medallion construction, maturity promotion, public Hugging Face publication, comparison, framework projection, gap analysis, re-analysis and reporting may proceed without manual approval when their machine-evaluable gates pass.

The system does **not** convert uncertainty into approval requests. It records uncertainty and continues wherever safe. A finding may therefore be published as provisional even when it is not strong enough to be promoted to a high-confidence assertion.

## Autonomy levels

| Level | Evidence state | Autonomous behaviour | Output treatment |
|---|---|---|---|
| **A0 — mechanically verified** | Deterministic/programmatic evidence, complete provenance, replayable | Full autonomy | `verified` |
| **A1 — robustly triangulated** | Independent qualified methods agree and scope/authority/time/source gates pass | Full autonomy | `high-confidence` |
| **A2 — supported but incomplete** | Source-grounded and at least one qualified method, but triangulation/coverage incomplete | Complete and report autonomously | `supported-needs-verification` |
| **A3 — provisional/conflicted** | Material disagreement, ambiguity, incomplete comparability or weak coverage | Complete and report; do not silently upgrade | `provisional-needs-additional-verification` |
| **A4 — insufficient evidence** | Evidence cannot support a defensible proposition | Abstain on that proposition and continue the remainder | `not-determined` |

Confidence is **claim-level**. One gap analysis may contain A0/A1 findings beside A2/A3 findings. The report-level summary must expose the distribution of evidence states and coverage rather than collapse them into one opaque confidence score.

## Confidence composition
Confidence is based on evidence dimensions, not model self-confidence. At minimum:

- source identity and fixity;
- exact source-span support;
- authority/scope applicability;
- temporal compatibility;
- retrieval coverage;
- method independence;
- model/method benchmark performance;
- agreement/disagreement;
- framework applicability;
- reproducibility/replay state.

A failed hard validity gate cannot be compensated for by high semantic similarity or agreement among models.

## Minimal exception gates
Human intervention is reserved for:

1. credentials that cannot be refreshed or supplied programmatically;
2. destructive/irreversible external mutations such as deleting or archiving canonical resources;
3. explicit requests for manual adjudication.

Redistribution and routine public release are **not** approval gates for this project. The maintainer has authority to redistribute the source corpus. SourceRight remains a dependency for provenance/source-quality metadata and reproducible source handling, not as a repetitive publication-approval mechanism.

Consequential interpretation is handled by evidence labels, provenance and clear caveats rather than blocking the computational workflow. Institutional users remain responsible for deciding how to act on outputs.
