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
