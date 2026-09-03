# Implementation status

This document distinguishes executable capability from roadmap intent. A passing local test is evidence of software behavior only; it is not a claim that a medallion corpus release has been completed or published.

## Implemented now

### Deterministic orchestration and assurance
- finite work-item and release state machines;
- medallion predecessor gates;
- A0–A4 claim-level confidence composition with non-compensatory hard gates;
- content-addressed hashing, manifests, receipts and append-only traces;
- bounded microtask compilation, compact prompt rendering, exact evidence-span/hash checks and minimal dependency-free schema validation;
- smallest-qualified-route selection contract;
- loopback-only OpenAI-compatible/llama.cpp adapter with structured-output verification.

### Corpus and medallion substrate
- closed Source Census v1 covering 28 official public source surfaces across ACT, NSW, NT, QLD, SA, TAS, VIC and WA plus Commonwealth comparators, with a hash-bound completion receipt and frozen Bronze publication contract;
- deterministic source-census receipt generation and an active 28-surface Bronze capture queue;
- partial document-level portal discovery evidence, including 213 current Safer Care Victoria publication results, 20 mandatory WA Clinical Governance/Safety/Quality policies, 20 SA Health policy domains, a 100-record ACT Health transparency-page snapshot, NSW's living Patient Matters manual, and the distributed NT Health Digital Library boundary;
- bounded HTTPS capture into SHA-256 content-addressed storage with HTTP provenance receipts;
- portal link discovery for likely policies/guidelines/procedures/frameworks;
- Bronze local ingest and deterministic Bronze manifests;
- Hugging Face Bronze candidate packaging with byte re-verification;
- Hugging Face public upload/remote-revision verification script for use when credentials are supplied;
- dependency-free Silver text/HTML normalization;
- optional parser hooks for PyMuPDF/pypdf and python-docx without making those parsers authoritative before benchmark qualification;
- optional spaCy exact-offset NLP projection for sentences, modality spans, jurisdictions, frameworks, configured concepts and policy roles; rule-only spaCy is explicitly non-independent triangulation evidence;
- deterministic Gold modality, timeframe and conservative simple actor/action/object extraction;
- transparent Platinum baseline similarity/comparability primitives that explicitly do not claim semantic equivalence;
- rebuildable Bronze→Silver→Gold→Platinum policy graph projection with checksum manifests;
- path-preserving GraphRAG retrieval using lexical seeds today and an explicit hook for later qualified semantic seed scores;
- finite release qualification receipts.

### Local and sensitive comparison
- network-free local document preparation, including optional spaCy feature and graph generation;
- institution-owned gap runner against a pinned public Gold JSONL baseline;
- portable `policy-gap-analysis` Agent Skill patterned on `rcagent`;
- content-addressed offline bundle builder/verifier;
- dependency-free Python zipapp build for portable execution;
- local model manifest contract and task-specific benchmark harness.

### CI/CD and automation
- 106 deterministic tests currently pass; the package is at 97% branch-aware coverage in the current public-corpus execution state;
- context/security/dependency-review workflows;
- Test-Goblin-style unit/integration/smoke/property/contract matrix;
- 95% branch-coverage target in CI;
- deterministic modality benchmark in CI;
- package build lane;
- scheduled source-health portal capture without medallion promotion;
- explicit Bronze Hugging Face publication workflow;
- SHA-pinned Actions and disabled checkout credential persistence.

## Implemented but not yet qualified for production medallion promotion

The following code exists but its production route still requires the relevant track benchmark or corpus gate:

- statistical spaCy pipelines and any use of them as independent triangulation evidence;
- semantic/vector seeding of GraphRAG and advanced graph reasoning/community summaries;
- PDF and DOCX parsers;
- lexical Platinum candidate matching;
- local generative inference;
- semantic assertion extraction beyond conservative deterministic clauses;
- institutional gap analysis beyond the deterministic baseline;
- automatic Hugging Face publication of a real Bronze release.

These remain deliberately unable to upgrade evidence merely because they execute successfully.

## Current public-corpus release state

- **T01 / Source Census v1:** completed. The release is intentionally a finite census of official source *surfaces*; individual-document completeness is a Bronze obligation.
- **T02 / Bronze v1:** active. Twenty-eight source surfaces are queued, but zero original payloads have been captured in this execution environment, so Gate B correctly remains closed.
- **T03 / Silver v1, T04 / Gold v1, T05 / Platinum v1:** production status remains planned because predecessor gates are non-compensatory.
- **Shadow clinical-governance slice:** 9 source observations → 9 shadow Silver segments → 48 shadow Gold concept candidates → 9 Platinum preview rows → 63-node/96-edge graph. It is explicitly `not_a_medallion_release`.
- **Hugging Face:** the four intended public dataset repositories do not yet exist. The authenticated connector exposes no dataset write action, and a `cpu-basic` Hugging Face Job attempt returned HTTP 402, so no upload is claimed. Publication candidate contracts and remote-verification machinery are ready.

## Genuinely deferred

The remaining work is now predominantly data acquisition and empirical qualification rather than architecture:

1. execute the networked 28-surface Bronze queue; recursively enumerate all in-scope public documents and assign every discovery a captured/duplicate/superseded/unavailable/out-of-scope disposition;
2. publish and remotely verify the real public Bronze Hugging Face release;
3. benchmark parser combinations on the captured PDF/DOCX/HTML corpus and select the qualified Silver route;
4. construct/adjudicate Gold extraction benchmarks, including jurisdiction and temporal hold-outs;
5. benchmark lexical, embedding, GraphRAG seed, cross-encoder, NLI and candidate generative methods on real comparison pairs;
6. choose and pin the smallest passing local models/quantizations;
7. generate and remotely verify the real public Silver, Gold and Platinum Hugging Face releases;
8. qualify the final institutional runner against those releases;
9. perform workstation-specific throughput/memory tuning only for any offline bundle that includes a local model runtime.

The intended local burden is therefore installation/selection/tuning of already-defined components, not architectural or workflow development.
