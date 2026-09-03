# T03 — Silver parsing and lineage maturity


## Objective
Produce a complete, reproducible Silver representation of the qualified Bronze release.

## Must requirements
- Format-specific parsing for PDF, HTML and DOCX; other formats added only through explicit adapters.
- Parser benchmark and differential parsing on representative/adversarial documents.
- Preserve page/DOM/paragraph/table anchors and exact Bronze lineage.
- Extract headings, sections, lists, tables, definitions, references/citations and document metadata.
- Maintain extraction-loss and parser-disagreement ledgers.
- OCR only when embedded text is absent/defective and always with OCR provenance/confidence.
- CiteWeft integration for reference/citation structures.
- Reconstruct Silver deterministically from pinned Bronze and code.

## Gate S
No Gold production until all v1 formats are qualified, loss is accounted, lineage is reversible and benchmark thresholds pass.
