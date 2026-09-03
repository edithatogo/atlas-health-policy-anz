# Roadmap

The roadmap is maturity-gated and release-oriented, not merely chronological. No downstream medallion production starts until the preceding scoped release is qualified and closed. Planning, schemas, fixtures and benchmark design may occur early; production derivation may not.

Routine execution is confidence-gated autonomous. Weak or conflicting analytical evidence is labelled A2/A3 or abstained A4 rather than converted into approval spam.

## Phase 0 — Foundation v1
- **T00** Conductor/context, Git traceability, ecosystem/dependency governance, autonomy contract, finite-release semantics and comparison assurance. Active.

**R0 finish:** deterministic context and validation pass; all agreed architecture/assurance decisions are recorded; subsequent work has finite completion contracts.

## Phase 1 — Source Census v1
- **T01** Australian source census, source taxonomy and public Hugging Face publication contracts.

**R1 finish:** declared v1 source universe is closed at an observation cutoff; every expected source surface has a disposition and capture strategy; Bronze schema/publication contract is frozen. New discoveries enter a later census release.

## Phase 2 — Bronze v1 to maturity
- **T02** Bronze acquisition/preservation/publication implementation and Bronze v1 maturity qualification.

**Gate B / R2 finish:** source census completeness for v1; all captured originals have fixity/provenance; recoverability proven; public HF Bronze release remotely verified; immutable manifest and completion receipt emitted. Silver production then becomes eligible.

## Phase 3 — Silver v1 to maturity
- **T03** Silver parsing, structure, citations and lineage; parser benchmarks and differential validation.

**Gate S / R3 finish:** all in-scope Bronze formats have qualified parsers or explicit failure states; extraction loss accounted; lineage reversible; Silver rebuild reproducible; benchmark thresholds pass; public HF Silver release and completion receipt verified.

## Phase 4 — Gold v1 to maturity
- **T04** Canonical bitemporal policy assertion/concept model, extraction and verification.

**Gate G / R4 finish:** assertion schema stable/versioned; representative/adversarial benchmark passes; source-span/authority/time lineage complete; uncertainty/abstention states validated; Gold rebuild reproducible; public HF Gold release and completion receipt verified.

## Phase 5 — Platinum v1 to maturity
- **T05** Cross-jurisdiction equivalence, contradiction, comparability and Platinum qualification.
- **T06** Comparison assurance, model/method triangulation and benchmark laboratory.
- **T08** Versioned analytical framework registry and plug-in projections.

**Gate P / R5 finish:** comparisons pass scope/authority/time/coverage gates; methods/models have pinned manifests; claim-level A0–A4 states are assigned; disagreements retained; framework versions pinned; clean replay produces materially identical outputs; public HF Platinum release and completion receipt verified.

## Cross-cutting capability development
- **T07** Agents, skills and workflows: typed contracts, fixtures, failure states, confidence-gated autonomy, orchestration, completion receipts and evaluation for T01–T06/T08.

## Reproducible gap-analysis platform v1
- **T09** Programmatic gap-analysis engine and institutional adapter contract. This track explicitly targets:
  1. independent repetition/verification/validation of any published gap analysis;
  2. comparisons against one or more policies across one or more jurisdictions;
  3. re-computation when policies, procedures, guidelines, standards or analytical frameworks change;
  4. programmatic institutional PPG gap analysis against state/national/selected comparator PPGs.

**R6 finish:** an independent user can define and replay a reference analysis from immutable manifests and obtain machine-readable and narrative outputs with provenance, coverage and A0–A4 evidence states.

## Living system and interfaces
- **T10** Atlas/API/CLI/MCP/Space interfaces over qualified datasets.
- **T11** Continuous source/framework/model drift detection, lineage-aware invalidation and versioned re-analysis.
- **T12** External research validation, policy diffusion/temporal studies and outcome-linked/causal analyses where defensible.

## Later experiments and candidate features — roadmap only
The items below are **not Conductor tracks** and should not be instantiated as tracks until a future prioritisation decision. They are hypotheses/features to evaluate after the core medallion and gap-analysis platform is working.

### Comparative-method experiments
- **Retriever bake-off:** BM25/FTS, sparse learned retrieval, multiple embedding families, ontology-assisted retrieval and hybrid/RRF approaches on frozen hard-case benchmarks.
- **Pairwise judge bake-off:** cross-encoders, NLI families, schema-grounded generative models and deterministic rule systems; compare accuracy, calibration, abstention and cost.
- **True model-diversity experiment:** test whether triangulation across genuinely different architectures/providers improves error detection versus ensembles of related models.
- **Confidence calibration:** compare conformal prediction, calibrated probabilities, empirical error bands and rule-based confidence composition for A0–A4 assignment.
- **Active-learning adjudication:** use disagreement/uncertainty to select the smallest number of human-adjudicated examples needed to improve benchmarks/models.
- **Adversarial mutation laboratory:** automatically mutate modality, actors, timeframes, exceptions, scope and negation to create controlled hard negatives and metamorphic tests.

### Representation and reasoning experiments
- **Knowledge-graph projection:** source→document→section→assertion→concept→framework→comparison graph, while retaining Parquet/Gold as authoritative.
- **Formal rule projection:** evaluate Datalog/logic/rules-engine representations for highly structured obligations and contradiction checks.
- **Policy genealogy:** version/wording lineage, borrowing/diffusion and clause ancestry across jurisdictions.
- **Equivalence-graph consistency:** triangle/cycle diagnostics to detect non-transitive or internally inconsistent equivalence classes.
- **Evidence-citation graph:** map which evidence/guidelines are cited across PPGs, identify citation convergence, staleness and uncited requirements.

### Analytical-feature experiments
- **Policy burden index:** mandatory actions, approvals, documentation, reporting, coordination and reading complexity, with sensitivity analysis over weighting assumptions.
- **Policy frontier/Pareto analysis:** safety/evidence concordance, administrative burden, autonomy, consumer participation and rural feasibility without imposing a single composite ranking.
- **Policy-change impact analysis:** identify exactly which downstream assertions, comparisons and institutional gap analyses invalidate after a document/framework change.
- **Unwarranted policy variation atlas:** distinguish explained variation (law/context/evidence) from residual variation requiring investigation.
- **Temporal responsiveness metrics:** lag from evidence/national-standard change to jurisdictional policy adoption.
- **Rural/remote feasibility simulator:** compare policy requirements with facility capability profiles and identify structurally impossible requirements.
- **Scope-of-practice atlas:** profession/task/supervision/credential/setting comparisons across jurisdictions.

### Research experiments
- **Outcome linkage:** only after reliable policy exposure definitions exist, link policy characteristics to aggregate outcomes with explicit confounding/identification limits.
- **Natural experiments:** interrupted time series, difference-in-differences, event studies or synthetic controls around discrete policy changes where assumptions are defensible.
- **Policy complexity versus performance:** test whether more prescriptive/burdensome PPG architectures are associated with better, unchanged or worse outcomes.
- **Diffusion studies:** estimate adoption networks and lag structures after national standards, coronial recommendations or major incidents.

### Tiny/local-model and automation experiments
- **Tiny-model specialization ladder:** benchmark sub-1B, 1–4B and compact discriminative models separately for modality, actor/action extraction, scope classification, pairwise equivalence and framework projection; store the smallest passing route per task.
- **Distillation/PEFT candidates:** derive compact task-specific classifiers or LoRA/adapter models only from adjudicated Gold/Platinum benchmarks, with untouched temporal/jurisdiction test sets.
- **DSPy/GEPA prompt compilation:** automatically optimize bounded microtask instructions/schema examples against training/validation metrics, then promote only after hidden hold-out and adversarial gates.
- **Local GGUF qualification matrix:** benchmark quantization levels, llama.cpp engines/backends and context budgets for quality/latency/RAM/energy trade-offs.
- **Schema-decoder bake-off:** compare engine-native JSON Schema, llama.cpp grammar conversion and XGrammar for structural failure rate, latency and supported-schema coverage.
- **Semantic cache experiment:** content-address model results by source+packet+prompt+schema+model+engine hashes to eliminate unnecessary repeat inference.
- **Browser-only sensitive comparator:** DuckDB-Wasm + Transformers.js/WebGPU/WASM, with public Atlas Parquet as baseline and no sensitive upload.
- **Portable Agent Skill distribution:** publish a policy-gap-analysis `SKILL.md` package with references/assets/checksums in the `rcagent` style for Codex/Claude/Gemini/Cursor-compatible clients, while retaining a purpose-built local runner as the authoritative state machine.
- **Public session-trace corpus:** emit sanitised public benchmark runs in Hugging Face Session Trace Simple Format for replay/audit; sensitive traces remain local.

### Free/public infrastructure experiments
- **HF Dataset Viewer as serverless query plane:** design public Silver/Gold/Platinum Parquet so the Hub's rows/search/filter/parquet/statistics/Croissant endpoints can answer common read-only queries without an Atlas backend.
- **HF Xet incremental publication:** exploit content-defined chunk deduplication for frequent versioned dataset commits while retaining release manifests/revisions as the authoritative identity.
- **HF webhooks:** evaluate Hub repo-change webhooks as a low-friction trigger into GitHub/local update orchestration; do not make webhook delivery authoritative or order-dependent.
- **ZeroGPU benchmark/demo:** use free personal ZeroGPU only for bounded interactive demos or occasional open-model qualification where the daily quota is sufficient; never make it required for routine production.
- **GitHub Artifact Attestations:** attest release packages, SBOMs and benchmark bundles; later evaluate reusable workflows + attestations toward SLSA v1 Build Level 3.
- **GitHub Agentic Workflows:** evaluate `gh-aw` for non-authoritative repository maintenance such as issue triage, stale-context detection, documentation/test suggestions and CI diagnosis. Deterministic Actions remain authoritative for builds, medallion promotion and evidence qualification.

### Product/interface experiments
- **Public benchmark/challenge set:** publish adjudicated difficult policy-pair examples on Hugging Face for reproducible method comparison.
- **Evidence badges:** machine-verifiable provenance/replay/coverage badges on Atlas outputs.
- **Local institutional runner:** container/package that maps local PPGs into the common contract without requiring public upload.
- **Policy compiler:** construct candidate policy clauses from selected qualified requirements/frontier positions with clause-by-clause provenance and explicit normative choices.
- **Change subscriptions:** notify users when an upstream policy/framework change invalidates or materially changes a saved analysis.
- **Interactive disagreement explorer:** expose why methods/models/frameworks disagree rather than displaying only a fused conclusion.
- **International extension:** add New Zealand and selected international health-system policy corpora only after Australian contracts are stable.

## Deferred application principle
Recommendation synthesis, candidate policy wording, implementation options and institution-specific decision support remain derived products. They may be generated autonomously with provenance and A0–A4 evidence labels; the system does not claim authority to make the institution's ultimate governance decision.
