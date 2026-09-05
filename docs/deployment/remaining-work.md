# Atlas deployment: completed integration and remaining data-product work

Updated 6 September 2026 (Australia/Brisbane). Canonical repository:
`edithatogo/atlas-health-policy-anz`.

## GitHub integration: completed at the named code revision

- [x] Restore the recovered application and retain both Git histories (PR #4).
- [x] Correct test-environment dependency selection (PR #5).
- [x] Resolve and commit a real dependency lock; execute dependency and security
  audits rather than skipping them (PR #6 and subsequent locked runs).
- [x] Integrate NZ/ANZ source/authority collections and expanded strict testing
  (PR #7).
- [x] Resolve Ruff, formatting, basedpyright and ty diagnostics without weakening
  configuration, lock or acceptance thresholds (PR #8).
- [x] Verify all four ordinary post-merge workflows on
  `f3ecbc3c40f6f1f6e458b04ec6bae7a6420cfa3c`.
- [x] Download and hash-check the matching quality artifact; reconcile test counts,
  runtime, coverage and source identity with the actual main-branch receipt.

The code import and software-quality repairs are no longer pending. The earlier
transport corruption, missing dependencies and lint/type failures are preserved
in Git history and dated receipts, not erased or reclassified as successes.
The evidence is `quality/github-integration-main-20260906.json`.

## Remaining finite milestones: not closed by software CI

1. **T00/T07 native dependencies.** Execute and qualify the pinned SourceRight,
   CiteWeft and Authentext integrations. Resolved identities and adapter contracts
   are not a native end-to-end execution result. Overall track states remain
   unchanged by this documentation closeout.
2. **T02 public HF deployment.** Verify scoped write access through repository
   secrets and independently verify public dataset creation, immutable revisions,
   anonymous downloads and object hashes. Do not publish secret values in chat,
   logs, source or PR text. This closeout does not inspect or provision secrets.
3. **T02 source acquisition.** Execute the selected `au-v1`, `nz-v1` or `anz-v1`
   configuration; qualify source adapters, document inventories, cross-host
   stores, pagination and failure dispositions. Configured profiles, directory
   counts and exhausted budgets are not document-level completeness.
4. **T02 Bronze v1 closure.** Complete the typed final release manifest,
   original-byte/provenance verification, explicit scope and coverage accounting,
   public remote verification and clean reconstruction. Source staging and
   software fixtures cannot satisfy this gate.
5. **T03 Silver v1.** Qualify parsing against captured originals, including offsets,
   reading order, tables, references and extraction-loss accounting; publish and
   verify the completed derivative release.
6. **T04/T05/T06/T08 Gold and Platinum.** Establish real extraction/comparison
   benchmarks, independent-method evidence and separate framework projections;
   preserve A0-A4 states, uncertainty and provenance before sequential release
   promotion. Software-quality improvements do not certify policy interpretation.

The future institutional/programmatic engine and living-update experiments remain
in existing tracks and roadmap entries. No new Conductor tracks or approval gates
are created. AU v1 remains a frozen initial inventory; NZ is now integrated in the
software and selected source collections, while production NZ corpus coverage is
not claimed. No live capture, HF write, mutation/prerelease experiment or medallion
promotion was executed as part of this GitHub closeout.
