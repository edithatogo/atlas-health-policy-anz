# Tech Stack and Comparison Assurance

All dependencies remain candidates until benchmarked and adopted through the relevant Conductor track. This document records the intended tool classes and default candidates, not an assertion that every package is already installed.

## Core runtime and data
- CPython 3.14, `uv` lock/reproducibility pattern.
- Git/GitHub: code, context, provenance, issues/change control and CI.
- Hugging Face Hub/Xet: public source/data/benchmark publication and model registry.
- Parquet + DuckDB: canonical tabular analytical substrate.
- JSON Schema + Pydantic: typed interchange and runtime validation.
- TOML/YAML: configuration/manifests.
- SHA-256 plus optional BLAKE3: fixity/content identity.
- WARC/WACZ (`warcio`/compatible tooling): material web capture context where appropriate.
- RO-Crate, Croissant, PROV and DCAT projections for Platinum/publication metadata.

## Acquisition candidates
- `httpx`: bounded HTTP acquisition with explicit timeout/retry policy.
- `warcio`: WARC construction/inspection.
- `selectolax`: deterministic DOM parsing.
- Playwright only for sources whose content cannot be captured from direct/document endpoints; browser capture is a last-mile adapter, not a default crawler.
- Source-specific adapters are preferred over a universal scraper.

## Document extraction candidates
No single parser is authoritative.
- PDF: PyMuPDF for page/text/geometry extraction; `pypdf` for independent metadata/text checks; Docling evaluated for layout/table-aware parsing.
- HTML: `selectolax` DOM extraction plus `trafilatura` as an independent main-text candidate where useful.
- DOCX: `python-docx` plus ZIP/XML-level checks for structures not represented by the high-level API.
- XLSX if encountered: `openpyxl` only after dependency qualification; workbook originals remain Bronze.
- OCR: OCRmyPDF/Tesseract only for genuinely image-only pages and with OCR provenance/confidence retained. OCR is never silently substituted for embedded text.

Differential parsing is required on benchmark/sample material: disagreement between parsers is surfaced, not averaged away.

## Structural and lexical comparison
- Unicode/whitespace/typographic normalisation with loss ledger.
- Exact hashes and normalized hashes for duplicate/version detection.
- `rapidfuzz` for token/string similarity and near-duplicate discovery.
- BM25/FTS (DuckDB FTS or a qualified BM25 implementation) for lexical candidate retrieval.
- Rule-based modality/authority/timeframe extraction using validated patterns and optionally spaCy components where they improve benchmark performance.

## Semantic candidate retrieval
Semantic methods only produce candidates unless independently qualified.
- `sentence-transformers` / Hugging Face Transformers for pinned embedding models.
- At least two materially different retrieval signals must be available for difficult comparisons: lexical BM25 and embedding retrieval; ontology/concept matches provide a third orthogonal signal where available.
- Candidate fusion should use a transparent method such as Reciprocal Rank Fusion rather than opaque score averaging.
- Lance/LanceDB may be used as a derived vector index; vector state is never authoritative.

## Pairwise equivalence and contradiction
A staged classifier is preferred:
1. deterministic scope/authority/temporal compatibility checks;
2. lexical/semantic candidate retrieval;
3. cross-encoder semantic similarity/reranking;
4. NLI entailment/contradiction model;
5. schema-constrained source-grounded generative judgment only for unresolved cases;
6. explicit adjudication state where methods disagree.

Potential model families are benchmarked rather than hard-coded. Model manifests record model ID, immutable revision, tokenizer, prompt/schema, inference parameters, hardware/runtime and source hashes.

## Generative model use
Generative models are prohibited from creating canonical facts without extractive provenance. Their role is:
- candidate structured extraction tied to verbatim source spans;
- difficult equivalence/contradiction adjudication;
- framework application where rules alone are insufficient;
- narrative synthesis from already-qualified tables.

Required controls:
- JSON/schema-constrained output;
- temperature 0 or otherwise deterministic settings where supported;
- quote/span verification against the source;
- no answer when evidence is unavailable;
- independent validation path;
- model/version/prompt receipt on every benchmarked or publication-facing run.

## Model triangulation
Triangulation is **selective and benchmark-driven**, not automatic majority voting.
- Prefer independent model families/providers or architectures for difficult cases.
- Run independent prompts without exposing one model's conclusion to another.
- Compare proposition, evidence spans and confidence, not just final labels.
- Shared agreement does not override a failed source/provenance/authority gate.
- Systematic shared error is assessed against an adjudicated benchmark.
- High-impact disagreement remains `conflicting_evidence`/`needs_adjudication`; it is not forced to consensus.

## Framework triangulation
Frameworks answer different questions and are retained as separate projections rather than combined into a single pseudo-objective score. Planned families include:
- NSQHS and National Model Clinical Governance Framework;
- legal/regulatory concordance;
- evidence concordance;
- human factors and sociotechnical systems;
- Safety-I/Safety-II/resilient healthcare;
- implementation science;
- consumer partnership/co-production;
- equity and cultural safety;
- rural/remote feasibility;
- workforce/scope of practice;
- policy burden/administrative complexity;
- readability/accessibility.

Where two frameworks genuinely operationalise the same construct, convergence can be reported. Otherwise the system presents a multi-dimensional profile, not a vote.

## Evaluation metrics
Selection gates use task-specific metrics, including:
- source discovery recall and census disposition completeness;
- parser span/page/table fidelity and loss rates;
- extraction precision/recall/F1 and exact-span match;
- equivalence/contradiction precision, recall, macro-F1 and confusion matrices;
- ranking Recall@k/MRR/nDCG where candidate retrieval is relevant;
- calibration/Brier/ECE for probabilistic outputs where available;
- temporal/scope/authority error rates;
- abstention quality and unresolved-case rate;
- inter-method/model disagreement rates;
- mutation/property/metamorphic tests for invariants.

## Mandatory quality dependencies
SourceRight, CiteWeft and Authentext remain governed dependencies. Their outputs supplement but do not replace medallion/source validity gates.
