# Source-packet integration: 10 September 2026 (Australia/Brisbane)

Existing tracks **T02** (public original acquisition/staging) and **T07** (bounded
execution). No new track, authority/source-census scope, dependency or promotion
threshold is introduced. No whole-track closure is implied.

## Starting observation

Main revision `e4faa5fa7dc2198adbfc108f5d484a2b21bc8c98` includes PR #10's eight
original Queensland PDFs. The prior integration closeout's zero-payload statements
remain true of that earlier pass, not current corpus holdings. The source packet
has 15 outcomes, eight captured originals, seven failures and a separate full-
report URL gap. The evaluation that motivated those sources stays outside Atlas.

## Finite work package

1. Verify the existing request and capture-manifest against independent registry
   pins, original PDF bytes, exact membership and declared failure dispositions.
2. Build deterministic, source-only content-addressed staging packages with all
   provenance and no evaluation files. Do not manufacture crawler receipts.
3. Publish through the existing public HubStore only with a usable write credential;
   pin the returned revision and anonymously reconstruct all uploaded members.
4. Run byte mutation, metadata/membership corruption, forged-completeness,
   idempotence, private-target and replay negative controls under the unchanged
   strict/locked toolchain; exercise the actual committed originals offline.
5. Integrate PR verification and trusted-main publication with terminal evidence
   states. Record credential absence without approval spam or publication claims.

Implemented entry points are `packet_ingestion.py`, `packet_staging.py` and
`scripts/source_packets.py`. Contracts are in the independently pinned packet
registry and two source-packet schemas. Read `docs/SOURCE_PACKET_STAGING.md` for
commands, scope, trust assumptions and the exact completion boundary.

## Qualification boundary

The implementation's tests and candidate receipts are evaluated at their exact
source/PR revisions. Normal PR workflows and post-merge source-packet job outcomes
are authoritative for hosted acceptance; a local pass is not a hosted pass.
The temporary read-only environment export workflow is removed from the final
tree. No source originals, existing strict settings or lockfile are modified.

Packet staging is **not** Bronze v1 qualification, policy currency/compliance,
parser benchmarking or an executed native SourceRight/CiteWeft/Authentext audit.
The core AU/NZ acquisition collections remain unchanged. T02 still owns their
live capture, final release manifest and clean public reconstruction; T03-T05
remain sequentially gated. Missing HF credentials leave publication blocked,
not complete. PR/run receipts record any actual publication separately.
