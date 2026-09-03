# T09 — Reproducible and institutional gap-analysis engine


## Objective
Deliver a programmatic, reproducible gap-analysis engine over qualified Platinum primitives.

## Required use cases
1. Anyone can repeat, verify and validate a published gap analysis from pinned manifests.
2. A user can select one or more target policies, one or more comparator policies/jurisdictions and one or more analytical frameworks.
3. A prior analysis can be updated when PPGs or frameworks change, with old results retained and differences explained.
4. An institution can map its own PPGs into the common contracts and compare them programmatically against state/national/other baselines.

## Must requirements
- Analysis specification is machine-readable and includes observation date, scope, corpus revisions, frameworks, model/method manifests and thresholds.
- Output includes machine-readable gap matrix, evidence bundle, replay command, coverage/uncertainty and human narrative.
- Institutional adapters can run locally/private while consuming public Atlas baselines; private local inputs do not need to be uploaded to the public Atlas.
- Gap types distinguish true missing requirements from non-retrieval/coverage uncertainty and intentional local divergence.
