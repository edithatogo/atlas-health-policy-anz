# Workflow Catalogue

T07 will implement these as deterministic workflows with resumable state, evidence receipts and confidence-gated autonomy.

## WF-00 Finite work-package executor
Resolve release scope → enumerate acceptance criteria → execute dependency graph → maintain resumable checkpoint state → run qualification → emit completion receipt → close release. Optional enhancements are deferred rather than allowed to keep a release perpetually open.

## WF-01 Bronze source-to-publication
Source census → capture → CAS/WARC → fixity/provenance/SourceRight metadata → Bronze validation → public HF publication → remote verification → Bronze completion receipt. No routine manual publication gate.

## WF-02 Silver construction
Pinned Bronze release → format routing → parser ensemble → structural normalization → lineage/loss accounting → differential validation → evidence-state assignment → Silver maturity gate → public release/verification → completion receipt.

## WF-03 Gold assertion construction
Pinned Silver release → assertion candidates → exact-span verification → authority/modality/time normalization → concept mapping → uncertainty/autonomy states → Gold benchmark/gate → public release/verification → completion receipt.

## WF-04 Platinum comparison
Pinned Gold release → query/problem definition → comparability qualification → candidate retrieval → equivalence/contradiction classification → triangulation → framework projections → claim-level A0–A4 classification → coverage/uncertainty → Platinum gate → public release/verification → completion receipt.

## WF-05 Reproducible gap analysis
Select target corpus + comparator corpus(es) + framework(s) + observation date → freeze manifests → run WF-04 primitives → emit machine-readable matrix, provenance bundle, claim-level evidence states, narrative report and replay command. Provisional findings are included with explicit verification status rather than withheld.

## WF-06 Living update
Detect source/framework/model change → capture new Bronze objects → identify affected lineage graph → rebuild only invalidated derivatives → re-run impacted benchmarks/comparisons → produce change report; never silently overwrite prior releases.

## WF-07 Institutional gap analysis
Import institution PPG corpus under an institution-owned deployment → normalize through common contracts → compare against selected state/national/other-jurisdiction baselines → export gaps and evidence. The public Atlas need not ingest private institutional documents; programmatic compatibility is the requirement.

## WF-08 Independent verification
Clean environment → fetch pinned public Bronze/manifests/code/model revisions → rebuild layers → rerun gap analysis → compare checksums/record counts/metrics → produce verification receipt.

## WF-09 Confidence adjudication
For each candidate finding: deterministic validity gates → independent method evidence → optional model triangulation → calibration/benchmark lookup → assign A0–A4 → record reason codes. A2/A3 remain reportable; A4 abstains. No model majority vote can upgrade a failed hard gate.

## WF-10 Tiny-model microtask execution
Resolve work-item state → deterministically select one open question/method → compile microtask packet → run deterministic method or smallest qualified local model with constrained decoding → verify schema/span/hash/scope → reason-coded context expansion or bounded escalation if needed → assign A0–A4 → checkpoint terminal state. The model never chooses the next workflow state.

## WF-11 Local sensitive comparison
Pre-pin public baseline, code, model and schemas → disable network by default → ingest private document locally → create Silver/Gold-compatible local derivatives → run WF-10 and selected gap-analysis workflow → retain private evidence/embeddings/prompts/traces/results locally → export only when the operator explicitly requests it.

## WF-12 Browser-private comparison experiment
Load public baseline Parquet into DuckDB-Wasm → keep user document in browser memory/local file APIs → perform deterministic retrieval plus qualified Transformers.js/WebGPU/WASM inference → generate local gap-analysis package. No server receives the sensitive document. This remains experimental until browser security, memory and benchmark gates pass.
