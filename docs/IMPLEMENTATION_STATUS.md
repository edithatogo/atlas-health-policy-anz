# Implementation status

Updated 6 September 2026 (Australia/Brisbane). This file separates implemented
software and measured hosted qualification from unfinished data-product work.

## Current GitHub status

The application and recovered history are on `main`. PR #8 is merged at
`f3ecbc3c40f6f1f6e458b04ec6bae7a6420cfa3c`. Its post-merge Context CI, Strict
Python Quality, Test-Goblin and Security and Context workflows all passed.
See `quality/github-integration-main-20260906.json` for exact run identities and
artifact verification, and `conductor/github-integration-20260906.md` for the
current context. Later documentation revisions require their own checks.

The earlier local-only test and unresolved lint/type descriptions are historical,
not the current engineering state. Evidence under
`evidence/engineering/recovery-20260905/` and the dated quality receipts is retained.

## Implemented software and limits

| Component | Implemented behaviour | Qualification boundary |
|---|---|---|
| Capture/crawl | HTTPS/redirect checks, bounded bodies and retries, CAS, checkpoint lineage and dispositions | Live adapter and document-corpus completeness remain unqualified |
| HF staging | Immutable packages, exact inventories, anonymous re-download/hash verification and conditional pointers | Mocked SDK tests are not live publication evidence |
| Remote assessment | Pinned-source verification and readiness reporting | Not completed final Bronze closure |
| Institutional comparison | Reference-to-local primary matrix, reverse view, input-bounded confidence | Conservative lexical candidates; no compliance certification |
| Integrity | Validated JSON/object boundaries, duplicate/non-finite rejection, hashes, safe paths and atomic writes | Hashes establish fixity, not semantic truth or signatures |
| Local model runtime | Loopback endpoint checks, no ambient proxy, redirect refusal and response budgets | Not an OS sandbox or empirical model qualification |
| Portable delivery | Bundled registries, deterministic zipapp and clean-tree delivery checks | No claim of fleet-wide platform qualification |
| GraphRAG | Rebuildable graph and path-preserving lexical-seed evidence retrieval | No qualified semantic graph inference |
| spaCy | Optional rule features, exact offsets and configured concepts, including macrons | No trained Maori-language claim or rule-based independence claim |
| NZ/ANZ sources | NZ jurisdiction, authority registry, collection-specific acquisition/assessment and framework references | Source registration is not a completed corpus or legal-applicability determination |
| Quality toolchain | Locked dependencies, strict Ruff/format/basedpyright/ty, pytest profiles, hosted security and SBOM | Scheduled mutation/prerelease experiments are separate from routine passes |
| SourceRight/CiteWeft/Authentext | Exact revision observations and thin adapter contracts | Native end-to-end qualification remains open |

PDF/DOCX routing uses captured MIME and original URI for extensionless CAS files.
Conflicting hints are rejected; unextracted DOCX tables are reported. Parser
layout, reading-order and loss-accounting qualification remains open.

The ANZ catalogue has 212 bodies/functions, with identity-checked membership in
nine declared official directory snapshots. Source selections contain 28 AU-v1,
81 NZ-selected, 192 deduplicated authority and 220 combined ANZ profiles. These
are different denominators; the NZ selection is not additive to the authority
collection. Open-ended categories retain their unknown coverage denominator.

## Latest measured hosted assurance

The exact main-branch quality artifact reports **348 unique tests**, zero
failures/errors/skips, **97.30% combined statement/branch coverage**, **98.19%
statement-only coverage** and **93.86% branch-only coverage**. The unchanged gate
is 95% combined coverage; 100% critical-path coverage is not universally achieved.
The parallel lane repeats tests and does not increase the unique count.

The declared Python 3.14.6 environment and committed lock were used without a
host-compatibility override. Ruff ALL/preview, formatting, strict basedpyright and
strict ty pass over src/scripts/tests. Full-history Gitleaks, actionlint,
pedantic zizmor, CodeQL, locked vulnerability auditing and SBOM generation passed.
The five-case deterministic modality benchmark passes but does not qualify a
clinical/legal comparison model. No trained-model bake-off or policy-effect
result is claimed.

## Remaining production state

| Milestone | State |
|---|---|
| T00 Foundation | Active; GitHub/runtime/strict CI integration done, native ecosystem qualification still open |
| T01 AU Source Census v1 | Closed finite 28-surface inventory, not exhaustive document census |
| T02 Bronze v1 | Active; live publication, acquisition and final release closure remain open |
| T03 Silver v1 | Gated on qualified Bronze and parsers |
| T04 Gold v1 | Gated on Silver and extraction qualification |
| T05 Platinum v1 | Gated on Gold and comparison/framework qualification |
| T07 Agent/workflow engineering | Active; the bounded quality-integration work is complete, not the whole roadmap |

No track state or production gate is changed here. Shadow observations remain
quarantined and cannot substitute for captured originals.

## Previously claimed features still not established

Lineage-aware incremental invalidation, deterministic replay capsules, a systematic
metamorphic mutation generator, substantive framework projections, a benchmark-
trained model router and qualified structural/semantic comparisons were not
recovered and are not made implemented by strict-code remediation. Basic offline
bundles, route contracts, regression/property tests and lexical candidates are
not equivalent to those larger features.

See `docs/deployment/remaining-work.md` for the finite remaining acceptance work.
This GitHub closeout performed no HF write, live document capture or medallion
promotion and does not assert current external dataset or credential state.
