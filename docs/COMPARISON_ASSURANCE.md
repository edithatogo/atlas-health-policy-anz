# Comparison Assurance Contract

## Purpose
Cross-jurisdiction policy comparison is vulnerable to silent source gaps, document-version mismatch, authority mismatch, semantic overreach and language-model hallucination. The Atlas therefore separates discovery, extraction, candidate generation, equivalence judgment and normative interpretation.

## Core rule
A comparison is not qualified because a model can produce an answer. It is qualified only when the required evidence states and comparability gates are satisfied.

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

A difficult pair may be accepted automatically only if deterministic comparability gates pass and benchmark-qualified methods agree above predefined thresholds. If high-impact methods disagree, the record remains unresolved. A second or third model can help characterize disagreement, but cannot erase it.

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

Benchmark annotations must preserve source spans and adjudication rationale. Model/parser selection is versioned and revisited on material drift.

## Hallucination controls
- Retrieval and source selection precede generation.
- Generative extraction must return source spans that are programmatically verified.
- Unsupported output fields fail validation rather than being silently accepted.
- No model may infer a missing policy from absence in the retrieved corpus.
- Every comparison carries coverage and uncertainty states.
- Frameworks and models are versioned inputs to the result.
- Platinum products expose method/model manifests and enough lineage to reproduce them.
