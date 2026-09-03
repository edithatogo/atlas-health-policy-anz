# Australian Health Policy Atlas

Evidence-first, reproducible computational comparison of Australian state and territory health policies, procedures and guidelines.

## Architectural archetypes

- `edithatogo/archive-govt-nz`: acquisition, preservation, provenance, fixity, evidence gates, publication preparation.
- `edithatogo/global-medicines-atlas`: canonical comparative evidence, bitemporality, validity/uncertainty, DuckDB/Parquet, optional semantic retrieval, Atlas/API/CLI.

## Medallion model

- **Bronze**: immutable captured source evidence.
- **Silver**: reproducibly parsed and normalised documents.
- **Gold**: atomic, bitemporal, provenance-bearing policy assertions.
- **Platinum**: validated cross-jurisdiction comparisons and analytical products.
- **Diamond**: decision products, policy frontiers, recommendations and candidate reforms.

## Analytical ladder

Analyses progress only as comparability is established:

0. Identity and corpus coverage
1. Document structure
2. Atomic requirements
3. Concepts
4. Policy solutions
5. Governance architecture
6. Standards, legal and evidence concordance
7. Consensus, variation and outliers
8. Policy frontier and burden
9. Temporal diffusion and genealogy
10. Outcome-linked and causal analysis
11. Normative synthesis and policy design

See `conductor/roadmap.md`, `conductor/design.md` and `docs/COMPARISON_ASSURANCE.md`.


## Execution portability
- The orchestrator owns state; language models answer bounded typed microtasks.
- Deterministic and lexical methods precede tiny/local inference; larger models are fallbacks.
- Model-backed canonical outputs use constrained schemas plus exact source-span/hash verification.
- Sensitive institutional PPGs can be processed locally against pre-pinned public Atlas releases without upload.


## Executable core

For offline institutional use, see [`docs/LOCAL_QUICKSTART.md`](docs/LOCAL_QUICKSTART.md).

The repository now contains a dependency-light reference implementation of the governed workflow, including Bronze CAS/receipts, Silver text/HTML normalization, conservative Gold extraction, baseline Platinum comparison primitives, A0–A4 confidence logic, tiny-model packets, local/offline execution, institutional gap analysis, Hugging Face publication preparation and a portable zipapp. See `docs/IMPLEMENTATION_STATUS.md` for the exact qualified/deferred boundary.

Useful bootstrap commands (from a checkout):

```sh
PYTHONPATH=src python scripts/build_source_census.py
PYTHONPATH=src python scripts/benchmark_modality.py
PYTHONPATH=src python scripts/build_zipapp.py
python dist/au-health-policy-atlas.pyz classify-modality "The service must act."
```

## Project governance
Conductor is the authoritative context and delivery system. CI/CD and dependency policy are defined in `.context/ci.toml` and `docs/CI_CD.md`; tiny-model rules are defined in `.context/tiny-models.toml` and `docs/TINY_MODEL_EXECUTION.md`.

## GraphRAG and NLP

A rebuildable non-authoritative medallion graph, path-preserving GraphRAG retrieval, and optional spaCy exact-offset NLP projection are implemented. See `docs/GRAPHRAG_NLP.md`.
