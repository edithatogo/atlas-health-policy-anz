# Product

Australian Health Policy Atlas is an evidence-first computational system for sourcing, preserving, representing and comparing Australian state and territory health policies, procedures, guidelines and related governance instruments.

## Product thesis
Australian jurisdictions face many of the same clinical and governance problems under shared national standards, but implement them through different legal, policy and organisational architectures. The Atlas treats those policy estates as a versioned, computable corpus so that similarities, differences, gaps, outliers and policy solutions can be reproduced and tested rather than inferred from prose alone.

## Canonical progression
Implementation is strictly layer-gated:

1. **Bronze** — immutable source evidence, provenance and capture context.
2. **Silver** — reproducibly parsed and structurally normalised documents.
3. **Gold** — provenance-bearing, bitemporal atomic policy assertions and concepts.
4. **Platinum** — qualified cross-jurisdiction comparisons, gap analyses, consensus/outlier measures and framework projections.

Human-facing recommendations, candidate policy wording and implementation options are application products derived from Platinum; they are not authoritative medallion data.

The first substantive delivery is Bronze. Silver implementation must not begin until an explicitly scoped Bronze release passes its maturity gate. The same rule applies to every subsequent layer.

## Execution portability
The same canonical contracts must run from deterministic code through tiny/local models to larger model fallbacks. A language model is never the workflow controller: Conductor and program state are compiled into bounded typed microtasks. Institutional/sensitive documents can be projected locally into the same schemas and compared against pre-pinned public Atlas baselines without public upload.
