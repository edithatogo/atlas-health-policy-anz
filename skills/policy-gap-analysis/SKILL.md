---
name: policy-gap-analysis
description: Run a bounded, evidence-grounded comparison or gap analysis between health policies using the Australian Health Policy Atlas contracts. Load only the workflow/method references required for the current open question.
license: Apache-2.0
compatibility: Portable Markdown core; deterministic Atlas runner owns process state.
metadata:
  atlas-profile: portable-core
  atlas-skill-version: "0.1.0"
---

# Policy Gap Analysis

Use the Atlas runner as the system of record for workflow state. This skill supplies bounded instructions, not autonomous process control.

## Select one mode

1. **Scope** — define target, comparator(s), observation date and framework(s). Read `references/scope.md`.
2. **Compare** — inspect already-qualified Gold/Platinum inputs and answer one open comparison question. Read `references/compare.md`.
3. **Report** — convert qualified findings into a provenance-preserving gap matrix/narrative. Read `references/report.md`.
4. **Verify** — replay a pinned analysis and compare identities/results. Read `references/verify.md`.

If a request spans modes, run them in that order. Do not skip an unmet predecessor gate.

## Non-negotiable rules

- Use only supplied evidence for factual findings.
- Keep source evidence, extraction, comparison, framework projection and recommendation distinct.
- A0/A1 findings may proceed autonomously; A2/A3 remain reportable but carry verification labels; A4 abstains.
- Textual similarity is never itself policy equivalence.
- Absence from the retrieved corpus is not proof that a jurisdiction lacks a requirement.
- Never infer transitive equivalence.
- Preserve authority, scope and observation-time differences.
- Emit source span identifiers for material claims.
- Stop when the current open question is answered; do not stack methods for appearance of rigour.
