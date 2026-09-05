# T11 — Living update and invalidation system


## Objective
Make the Atlas a living, versioned system that detects changes and invalidates only affected downstream products.

## Must requirements
- Detect source additions, replacements, withdrawals, URL changes, metadata/schema drift, framework revisions and model/runtime changes.
- Preserve prior Bronze and derivative releases.
- Maintain lineage/invalidation graph Bronze→Silver→Gold→Platinum→gap analyses.
- Rebuild affected derivatives and rerun relevant benchmarks when a material method/model change occurs.
- Produce human and machine-readable change reports.
