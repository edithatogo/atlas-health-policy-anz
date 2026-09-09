# Queensland energy, health and appraisal source packet

Bounded original-document staging for Atlas T01/T02. This is NOT an economic evaluation repository. No evaluation plans, models, parameters, results, prompts or private data are included. The related evaluation stays local.

`request.json` is the finite source list. `originals/` contains unchanged native PDFs only when capture succeeds. `capture-manifest.json` records failures, hashes, final URLs, observed time, MIME, edition observations and attribution. `capture-manifest.sha256` establishes manifest fixity. Signature checks are not complete parsing, malware scanning, citation qualification or Bronze closure. No production medallion gate is changed and no HF publication occurs.

## Rights and attribution

Documents remain copyright of the State of Queensland and the named agencies. Retain all notices, follow each document's licence, and preserve cultural warnings and acknowledgements. Source documents are not relicensed under the Atlas software licence. QH default: https://www.health.qld.gov.au/global/copyright-statement ; Queensland default: https://www.qld.gov.au/legal/copyright . Document-specific terms override defaults. CC BY-ND copies remain unmodified; this packet does not authorize adapted republication. No separate reuse or relicensing of excluded logos, trademarks or third-party material is granted; no endorsement is implied.

Licence texts: https://creativecommons.org/licenses/by/4.0/ ; https://creativecommons.org/licenses/by-nd/4.0/ ; https://creativecommons.org/licenses/by/3.0/au/ .

## Acquisition and limits

One-off branch-specific workflow, no schedule, arbitrary URL input, paid-compute call or HF credential. Exact HTTPS host list, public-address check, bounded redirects/timeouts/bytes, rejection of HTML challenge pages. Downloaded bytes are never executed. Run the offline negative controls with `python -m unittest discover -s source-packets/queensland-energy-health-20260909 -p 'test_capture.py' -v`.

Reuse decision: adopt Atlas provenance/fixity and finite-release patterns. The existing HF-oriented production operation does not directly satisfy this explicitly requested GitHub-native source-only handoff; the isolated transport does not replace the canonical acquisition/parser stack. SourceRight/CiteWeft/Authentext end-to-end qualification is not claimed for this transport packet.

Known census gap: a full QSDR PDF URL was not recovered during bounded lookup. A summary is not substituted for the strategy. Inaccessible procurement or equity PDFs remain explicit failures. New sources or source changes enter an amendment or next packet, not silently rewritten originals.

The separate dependency artifact contains only the already selected public Conductor revision, enabling a local checkout without uploading the evaluation. It is not an Atlas submodule or ecosystem-dependency installation.
