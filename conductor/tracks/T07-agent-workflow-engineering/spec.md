# T07 — Agents, skills and workflow engineering


## Objective
Develop the reusable agents, skills and workflows needed to execute the medallion and comparison roadmap safely.

## Must requirements
- Implement typed contracts for every agent in `agents/catalog.md` with explicit inputs, outputs, abstention/failure states and authority limits.
- Implement versioned skills in `skills/catalog.md` with deterministic fixtures and tests.
- Implement resumable workflows in `workflows/catalog.md` with evidence receipts and idempotent/retry behavior where applicable.
- Separate candidate-generating agents from verifying/gating agents.
- Red-team fixtures target hallucination, source omission, false equivalence, temporal mismatch, authority mismatch and silent fallback.
- Model-backed agents require benchmark qualification and immutable model/prompt manifests.
- SourceRight, CiteWeft and Authentext adapters are shared skills rather than duplicated implementations.
- Workflows implement A0–A4 confidence-gated autonomy and do not request approval for routine reversible operations.
- Finite release closure is implemented as a first-class workflow with machine-verifiable completion receipts.
- Implement a deterministic microtask-packet compiler conforming to `schemas/microtask-packet-v1.json`; language models never own workflow state or unbounded method selection.
- Qualify tiny/local model routes per task class with schema-constrained decoding, context budgets, explicit stop rules and programmatic span/hash verification.
- Provide a portable policy-gap-analysis skill package patterned on `rcagent`: short selector skill, bounded references/assets, host-owned permissions/state, and offline/private execution compatibility.
- Record reproducible model-call/session traces for public benchmark runs while defaulting sensitive traces to local-only storage.
