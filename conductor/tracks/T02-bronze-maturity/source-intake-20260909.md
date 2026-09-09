# Bounded Queensland policy-original intake, 9 September 2026

This additional finite source-document work package belongs to T02. It does not close T02, amend the previously closed source census, or promote a medallion layer. The owner expressly requested original public documents in this repository. No institutional evaluation, model, assumptions, findings, agent prompts or local project plans were transferred.

## Scope and method

The request lists 18 government PDF URLs under `data/source-intake/qld-energy-resilience-20260909/request.json`. The one-shot workflow at commit `3b80a8579ef4c9f47680c14679daa94e52311fbc` reused the native `capture_url` boundary, permitted only the named hosts, limited individual bodies to 32 MiB and the collection to 200 MiB, and rejected non-PDF or incomplete responses. It did not crawl, bypass access controls, contact credentialed publisher endpoints, extract text, or write to Hugging Face.

## Observed outcome

- [x] All 18 named requests have a captured or explicit failure disposition.
- [x] Ten unchanged original PDFs, totalling 18,318,626 bytes, are stored in the source-document collection.
- [x] All ten were anonymously re-downloaded from exact source commit `f5e6761286d57e78715bbe9ba6e802982676deb9` and their lengths and SHA-256 values matched.
- [x] Durable capture and verification receipts distinguish the initial capture snapshot from subsequent remote verification.
- [x] Only the source-intake request, original-document collection and this T02 work-package record remain as net changes; the completed one-shot workflow was removed from the final tree.
- [x] The public Conductor dependency at `137c1e41ff9c1dc75ff277b9582460a0bd8c4768` was exported in a separate artifact without local project data.
- [x] Eight original documents remain unavailable from these attempts; no claim of complete document delivery or whole-track completion is made.

The ten-object transfer is complete and verified. The broader 18-document acquisition remains partial. See `data/source-documents/qld-energy-resilience-20260909/intake-result.json`. Native SourceRight/CiteWeft/Authentext qualification and legal applicability were not executed and are not implied by file integrity checks. Original notices and credits are retained; no altered or extracted full-text version is distributed.
