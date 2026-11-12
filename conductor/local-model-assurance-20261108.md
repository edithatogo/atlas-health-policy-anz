# Local-model qualification in the Policy Atlas — 8 November 2026

**Status: planned work within existing T06 comparison assurance, T07 agents and T12 research.** The Atlas remains an evidence-first policy retrieval/comparison product, not an authoritative legal or compliance determination service. Do not create a competing model catalogue: consume exact-revision qualification manifests from [models_lang](https://github.com/edithatogo/models_lang).

## Implementation sequence

1. Reuse existing Bronze/Silver/Gold/Platinum source-maturity boundaries, local comparison, provenance and GraphRAG; preserve organisation-neutral authority/version identifiers. Build synthetic and public-rights-reviewed policy pairs with superseded/current clauses, jurisdiction, mandatory/discretionary wording, contradictory clauses, missing provisions and applicability caveats.
2. Benchmark deterministic extraction and lexical/graph retrieval first. Then compare small Liquid LFM3 extraction, d1 bounded decisions and larger local reasoning models for obligation classification, source span fidelity, modality, negative obligations, missing provisions and equivalence assessment. Require `abstain` and uncertainty outputs.
3. Compare retrieved-context and full-context runs on the same question, with equal budgets and no hidden reliance on future versions. Score false equivalence, missed conflicting obligations, temporal/jurisdiction mistakes, unsupported citations, human reviewer time and calibration on held-out authorities.
4. Keep sensitive institutional policies local; disable external fallback, document endpoint egress constraints and reject mutable checkpoint aliases. Public HF exports only where documented publisher rights allow; dataset-estate-registry stays authoritative for HF dataset identity.
5. Consume `models_lang` versioned qualification records but run Atlas-specific evaluation and approval. Do not treat model agreement or long context as proof of legal effect.

## Acceptance

First agent slice: 20+ rights-cleared policy contrast cases, source-span gold labels, a runner adapter with deterministic and small-model baselines, and documented negative cases; all statuses honestly marked planned until executed. Subsequent human adjudication required before superiority claim or operational use. Feed evidence back to T06/T12 and avoid duplicate task hierarchies.
