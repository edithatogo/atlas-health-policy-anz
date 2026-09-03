# Workflow

1. Load deterministic context and the active Conductor track.
2. Confirm the current medallion maturity gate. Downstream production work is blocked if the preceding layer is not qualified.
3. Reconcile track spec, plan, metadata, decisions and evidence.
4. Discover/reuse ecosystem capabilities before implementation.
5. Freeze source/code/framework/model revisions needed for the unit of work.
6. Implement the smallest coherent change using typed contracts and explicit failure/abstention states.
7. Run the applicable deterministic, differential, benchmark, SourceRight, CiteWeft and Authentext gates.
8. Record machine evidence, uncertainty, coverage and unresolved limitations.
9. Commit with a scoped message; do not rewrite history once receipts cite the commit.
10. For authorized public data publication, build locally, publish to Hugging Face, then verify remote revision/bytes/metadata before claiming success.
11. Update track status, maturity state and changelog only when evidence supports it.
