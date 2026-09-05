# GraphRAG and spaCy NLP architecture

## Status

The repository now contains executable, dependency-light graph projection and
GraphRAG retrieval plus an optional spaCy NLP adapter. These are **derived
analysis/index layers**. They do not replace the canonical medallion records or
upgrade evidence merely because a graph/NLP method produced a plausible result.

## Progressive medallion graph

The graph becomes richer as each medallion layer matures:

| Layer | Graph projection |
|---|---|
| Bronze | source → captured object/version/provenance |
| Silver | source/document → exact segment/section/citation anchor |
| Gold | segment → assertion → jurisdiction/concept/framework |
| Platinum | assertion ↔ comparison finding; later citation, equivalence, genealogy and framework graphs |

Canonical JSONL/Parquet/manifests remain authoritative. `nodes.jsonl` and
`edges.jsonl` are checksum-addressed projections with `authoritative: false` and
may be deleted/rebuilt at any time.

## GraphRAG

`graphrag.retrieve_graph_context()` implements a transparent retrieval path:

1. lexical seed scoring over graph node text/properties;
2. optional externally supplied semantic seed scores from a later qualified
   embedding/sparse/reranking stack;
3. bounded graph expansion (default two hops);
4. relation-specific deterministic weights;
5. explicit path receipts for every returned node;
6. recovery of exact Silver evidence segments on the returned paths.

This keeps GraphRAG useful to very small models: the model receives a compact
set of source-grounded evidence plus the path explaining why it was retrieved,
rather than a large graph dump or an opaque generated community summary.

Graph distance/proximity is **candidate evidence only**. It cannot create a
canonical equivalence, override a modality difference, or bypass scope,
authority, temporal or provenance gates.

## spaCy NLP

`nlp.analyse_with_spacy()` supports:

- sentence segmentation;
- exact character offsets;
- normative modality spans;
- jurisdiction and framework references;
- configured policy concepts and workforce/role phrases;
- later use of a pinned statistical spaCy model for parser/NER/lemmatisation
  features where benchmarked.

The default blank-English + EntityRuler path is deterministic and useful for
normalisation/concept linkage, but it overlaps with the Atlas regex/rule layer
and is therefore explicitly marked `independent_method: false`.

A statistical spaCy pipeline is marked as a *potentially* independent method,
but can only enter confidence triangulation after its exact model/version is
recorded and it passes the relevant extraction/comparison benchmark. spaCy is
therefore a triangulation input, not an automatic extra vote.

## Local/sensitive execution

`prepare-local --spacy --graph` can produce in one network-free run:

- Silver segments;
- conservative deterministic Gold candidates;
- spaCy exact-offset features;
- concept links;
- a local graph projection;
- a receipt with `network_used: false`.

The graph may then be queried with `graph-query`. If a qualified local
embedding model later supplies semantic seed scores, the same GraphRAG traversal
can use them without changing the canonical graph contract.
