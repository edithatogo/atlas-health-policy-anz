# T06 — Comparison assurance and triangulation laboratory


## Objective
Develop and validate the comparison methods/models so hallucination and false-equivalence risks are measured rather than assumed away.

## Must requirements
- Benchmark lexical, ontology, embedding, cross-encoder, NLI and schema-grounded generative approaches separately and in staged combinations.
- Use independent method signals with different failure modes; document dependence between methods/models.
- Evaluate at least two materially distinct model families for tasks where model triangulation adds value.
- Preserve independent prompts and source spans; do not expose one model's judgment to another before synthesis.
- Define calibration/abstention thresholds and high-impact disagreement rules.
- Test adversarial pairs: copied wording with changed scope; same requirement with changed terminology; superseded/current; guideline/mandatory; negation; exceptions; timeframes; role substitutions.
- Record immutable model revisions and inference manifests.
- No majority-vote ground truth.
- Shared-base-model variants are not counted as materially independent model families.
- Benchmark design includes jurisdiction and temporal hold-outs where feasible.
- Evaluate claim-level calibration/abstention and A0–A4 assignment, not only class accuracy.
