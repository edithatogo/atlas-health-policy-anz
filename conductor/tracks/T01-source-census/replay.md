# T01 Replay

1. Validate `data/sources/source-surfaces-v1.json` as JSON.
2. Confirm QLD, NSW, VIC, SA, WA, TAS, ACT and NT are present and at least one Commonwealth comparator is present.
3. Confirm every source has `source_id`, `jurisdiction`, `url`, `capture_adapter` and `disposition`.
4. Recompute SHA-256 of the registry and compare with `evidence/public-corpus/source-census-v1/completion.json`.
5. Validate the files/hashes in `evidence/public-corpus/source-census-v1/manifest.json`.
6. Re-run `scripts/validate_context.py`.

New source discoveries after the observation cutoff belong to Source Census v1.1 or later and do not reopen v1.
