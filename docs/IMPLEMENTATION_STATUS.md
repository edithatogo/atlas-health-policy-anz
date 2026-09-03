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
- governed seed registry covering ACT, NSW, NT, QLD, SA, TAS, VIC and WA official policy surfaces;
- deterministic source-census receipt generation;
- bounded HTTPS capture into SHA-256 content-addressed storage with HTTP provenance receipts;
- portal link discovery for likely policies/guidelines/procedures/frameworks;
- Bronze local ingest and deterministic Bronze manifests;
- Hugging Face Bronze candidate packaging with byte re-verification;
- Hugging Face public upload/remote-revision verification script for use when credentials are supplied;
- dependency-free Silver text/HTML normalization;
- optional parser hooks for PyMuPDF/pypdf and python-docx without making those parsers authoritative before benchmark qualification;
- deterministic Gold modality, timeframe and conservative simple actor/action/object extraction;
- transparent Platinum baseline similarity/comparability primitives that explicitly do not claim semantic equivalence;
- finite release qualification receipts.

### Local and sensitive comparison
- network-free local document preparation;
- institution-owned gap runner against a pinned public Gold JSONL baseline;
- portable `policy-gap-analysis` Agent Skill patterned on `rcagent`;
- content-addressed offline bundle builder/verifier;
- dependency-free Python zipapp build for portable execution;
- local model manifest contract and task-specific benchmark harness.

### CI/CD and automation
- 90 deterministic tests currently pass with 95.96% branch-aware package coverage;
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

- PDF and DOCX parsers;
- lexical Platinum candidate matching;
- local generative inference;
- semantic assertion extraction beyond conservative deterministic clauses;
- institutional gap analysis beyond the deterministic baseline;
- automatic Hugging Face publication of a real Bronze release.

These remain deliberately unable to upgrade evidence merely because they execute successfully.

## Genuinely deferred

The remaining work that cannot be responsibly completed before the live corpus exists is mostly empirical rather than architectural:

1. close the v1 source census and enumerate every in-scope document rather than only seed portals;
2. run complete live acquisition and qualify Bronze v1;
3. benchmark parser combinations on the captured PDF/DOCX/HTML corpus and select the qualified Silver route;
4. construct/adjudicate Gold extraction benchmarks, including jurisdiction and temporal hold-outs;
5. benchmark embeddings, cross-encoders, NLI and candidate generative models on real comparison pairs;
6. choose and pin the smallest passing local models/quantizations;
7. generate the real public Silver, Gold and Platinum Hugging Face releases;
8. qualify the final institutional runner against those releases;
9. perform workstation-specific throughput/memory tuning for any offline bundle that includes a local model runtime.

The intended local burden is therefore installation/selection/tuning of already-defined components, not architectural or workflow development.
