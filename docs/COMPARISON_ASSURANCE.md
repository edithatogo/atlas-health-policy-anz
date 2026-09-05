# Comparison Assurance Contract

## Purpose
Cross-jurisdiction policy comparison is vulnerable to silent source gaps, document-version mismatch, authority mismatch, semantic overreach and language-model hallucination. The Atlas therefore separates discovery, extraction, candidate generation, equivalence judgment, framework projection and normative interpretation.

## Core rule
A comparison is not qualified because a model can produce an answer. It is qualified only when required evidence states and comparability gates are satisfied. Evidence weakness downgrades the individual claim; it need not stop the rest of an analysis.

## Orthogonal methods
The planned comparison stack intentionally mixes methods with different failure modes:

1. **Deterministic identity and metadata checks** — jurisdiction, issuer, instrument type, version, dates, scope and status.
2. **Exact/normalized hashing** — duplicates and versions.
3. **Lexical retrieval** — BM25/token/phrase matching.
4. **Concept/ontology matching** — controlled concepts and synonym sets.
5. **Embedding retrieval** — semantic candidate discovery, never authority.
6. **Cross-encoder reranking** — pairwise semantic relevance.
7. **NLI** — entailment/contradiction/neutral evidence.
8. **Schema-constrained LLM assessment** — only after source spans are provided and only with explicit abstention/disagreement states.
9. **Framework projections** — independent analyses through legal, standards, evidence, sociotechnical, equity, rural and other lenses.

## Triangulation policy
Triangulation seeks robustness through *independent evidence paths*, not through counting model votes.

A difficult pair may be promoted to A1 automatically only if deterministic comparability gates pass and benchmark-qualified independent methods agree above predefined thresholds. A second or third model can help characterize disagreement, but cannot erase it. Shared-base-model variants are not counted as independent families for triangulation purposes.

If methods disagree, the system reports the result as A2/A3 with reason codes and continues. It does not manufacture consensus and does not require a manual approval simply to finish the analysis.

## Pairwise relation discipline
Equivalence is stored as qualified **pairwise evidence**. It is not assumed to be transitive. If A≈B and B≈C, A≈C must still be directly evaluated or remain unknown. Derived equivalence clusters must expose inconsistent triangles/cycles rather than hiding them.

## Coverage discipline
Every coverage claim has an explicit denominator and observation cutoff. Examples include:
- expected source surfaces captured / expected source surfaces in census;
- parsed documents / Bronze documents;
- verified assertions / extracted assertion candidates;
- comparator assertions with adequate candidate recall / comparator assertions in scope.

A percentage without a defensible denominator is not a qualification metric.

## Benchmark hierarchy
Production use requires a frozen benchmark containing representative:
- exact equivalents;
- partial equivalents;
- stricter/weaker requirements;
- contradictions;
- superficially similar but scope-incompatible clauses;
- same concept under different terminology;
- different concepts using similar terminology;
- superseded/current mismatches;
- legal versus advisory instrument mismatches;
- non-retrieval/coverage uncertainty.

Benchmarks should combine real adjudicated examples with controlled adversarial/metamorphic examples. Evaluation should include jurisdiction hold-outs and temporal hold-outs where feasible so a model cannot appear robust merely by memorising recurring local wording. Metrics are stratified by case type and jurisdiction, not just pooled.

## Confidence/autonomy
Evidence state follows `.context/autonomy.toml`:
- **A0** mechanically verified;
- **A1** robustly triangulated;
- **A2** supported but incomplete;
- **A3** provisional/conflicted;
- **A4** not determined/abstain.

These labels derive from provenance, comparability, coverage and benchmarked method evidence. Model self-reported confidence is non-authoritative.

## Hallucination controls
- Retrieval and source selection precede generation.
- Generative extraction must return source spans that are programmatically verified.
- Unsupported output fields fail validation rather than being silently accepted.
- No model may infer a missing policy from absence in the retrieved corpus.
- Every comparison carries coverage and uncertainty states.
- Frameworks and models are versioned inputs to the result.
- Platinum products expose method/model manifests and enough lineage to reproduce them.
- Descriptive comparisons are kept separate from normative recommendations.
