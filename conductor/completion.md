# Discrete Completion and Release Contracts

Implementation is organised into finite, closable releases. A phase is not "ongoing" once its declared scope and gates are satisfied. New discoveries after closure enter a subsequent release or the living-update workflow.

## Completion semantics
Each release has five states:

`planned -> executing -> candidate -> qualified -> closed`

- **planned:** scope and acceptance contract exist.
- **executing:** work is underway.
- **candidate:** all expected artefacts exist; qualification is running.
- **qualified:** non-compensatory gates pass and evidence bundle is complete.
- **closed:** release manifest, changelog, replay instructions and immutable identifiers are recorded. Routine downstream work may start.

A release may close with A2/A3 analytical findings if those findings are truthfully labelled. It may not close with missing required corpus objects, silent extraction loss, broken lineage, or unrecorded failures.

## Initial finite releases

### R0 — Foundation v1
**Finish:** Conductor/context, dependency governance, autonomy contract, track registry, comparison assurance, Git history and validation harness are internally consistent.

### R1 — Source Census v1
**Scope:** initial Australian state/territory health policy/procedure/guideline source surfaces plus declared national comparator sources.

**Finish:** source registry is closed at a declared observation time; each expected source surface has a disposition and capture strategy; Hugging Face Bronze publication schema is frozen.

### R2 — Bronze v1
**Finish:** every R1 in-scope object is captured or has an explicit failure/disposition; originals and web evidence have hashes/provenance; public Hugging Face Bronze release is uploaded and remotely verified; clean recovery from the release manifest succeeds.

### R3 — Silver v1
**Finish:** every Bronze v1 object is routed through a qualified parser or explicit unsupported/failure state; structural extraction loss is accounted; anchors/lineage are reversible; Silver release is reproducible and published/verified.

### R4 — Gold v1
**Finish:** canonical assertions/concepts exist for Silver v1 with source-span lineage and uncertainty states; benchmark and adversarial gates pass; all required records are reconstructible; Gold release is published/verified.

### R5 — Platinum v1
**Finish:** defined cross-jurisdiction comparisons and framework projections for the v1 corpus are comparability-qualified; methods/models are pinned; disagreements and A0–A4 evidence states are retained; replay reproduces the release; Platinum is published/verified.

### R6 — Gap Analysis Engine v1
**Finish:** a third party can specify target/comparator corpora and frameworks, reproduce a reference analysis from immutable manifests, and receive machine-readable plus human-readable outputs with evidence states.

## Scope discipline
- A release cutoff is explicit and immutable once closed.
- Later or newly discovered documents do not reopen a closed release; they create a new incremental release.
- Nice-to-have enhancements cannot block closure unless they were declared acceptance criteria before execution.
- Each release produces a machine-readable manifest, evidence bundle, changelog entry, replay command and completion receipt.
- Downstream releases consume immutable upstream release identifiers rather than mutable "latest" state.
