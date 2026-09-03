# Agent Operating Contract

This repository uses Conductor as the authoritative context-management and work-planning system.

## Context load order
Read `.context/project.toml`, then every `required_context` entry in order before consequential changes.

## Work discipline
- Every substantive change must belong to a Conductor track.
- Track requirements, plans, decisions, evidence and validation receipts must remain mutually consistent.
- Preserve source provenance and uncertainty; never infer absence from non-retrieval.
- Reuse before build. Consult `.context/ecosystem.toml` before creating overlapping functionality.
- SourceRight, CiteWeft and Authentext are mandatory quality-toolchain dependencies for source-bearing or publication-facing outputs.
- Do not use Git submodules for ecosystem dependencies; use thin adapters and exact-revision integration records.
- Human gates in `.context/project.toml` must not be auto-asserted as passed.

## Git discipline
- Keep commits scoped and descriptive.
- Do not rewrite history after an evidence receipt references a commit.
- Validation receipts should identify the commit they validate.
