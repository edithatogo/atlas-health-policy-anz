# Intake compatibility and acquisition preflight: 10 September 2026

Existing **T02/T07** work package. No new tracks or medallion release promotion.
Starting main: `9e0d389c80556bb93c0aecaaf1df587ee9387be6` (merged PR #13).

## Recovered publication-selection gap

The publication allowlist previously selected only the 15-record, eight-original
`queensland-energy-health-20260909` packet. An earlier preserved intake,
`qld-energy-resilience-20260909`, contains 18 requested records, ten captured PDFs
and eight explicit failures. Its request and manifest have a different layout and
schema, so it could not enter the same importer without an explicit adapter.

Both histories are now registered. The adapter reads the original request under
`data/source-intake/` and the original capture manifest and PDFs under
`data/source-documents/`. Independent metadata pins and the original source revision
remain explicit. Request/manifest bytes are retained verbatim in the standard
staging evidence paths; transient projections do not rewrite capture history.
Failure records only have a batch completion time, which is labelled as such.
Rights/attribution prose is copied, not converted into an invented licence grant.

The ten-PDF original tree `5036abfaaedfa3cde63f872138e94f35687224a6` and capture
manifest blob `22bc443acfe82f3123fdc96c084d6323028f6e95` match the independently
inspected source revision `f5e6761286d57e78715bbe9ba6e802982676deb9`. The previous
packet's specification and integrity-observation hash remain unchanged.

## Counts are histories, bytes and scope, not interchangeable denominators

| Measure across successfully verified packet observations | Value |
|---|---:|
| Registered packet histories | 2 |
| Requested source records across those histories | 33 |
| Successful original capture occurrences | 18 |
| Failed capture records retained | 15 |
| Distinct SHA-256 original byte objects | 10 |
| Distinct original bytes | 18,318,626 |
| Repeated successful byte occurrences | 8 |

Eight legacy PDFs are identical to eight in the earlier intake. The two additional
selected originals are the QRA strategic plan and disaster-resilience summary.
The summary is not the full strategy, which remains an explicit gap. No original
was newly fetched, copied into another Git directory or deleted in this change.
Per-packet staging still stores its own immutable package paths; the cross-packet
holdings report deduplicates counts, not remote path names or historical records.
The aggregate is scoped only to successfully verified observations, not all source
requests or the AU/NZ corpus. A later capture never erases an earlier failure.

## Execution fixes

The old scheduled Bronze preflight imported Python 3.14 syntax with the runner's
unspecified default Python. It now installs 3.14.6 before a dependency-free plan
compile. Relevant PRs run only that offline preflight; trusted-main guards keep
credentials and the capture matrix out of PR execution.

`capture_plan.py` binds exact source-policy hashes to a sorted matrix and a positive
integer invocation budget. It rejects empty, duplicate, invalid or oversized
selections and plans above 5,120 frontier attempts. The default ANZ plan remains
220 source profiles at 20 frontier attempts each (4,400), with at most three
capture jobs concurrently. This is not a bound on redirects, HF transfers or total
runner cost; no live capture or free-service quota is inferred from a plan.
Plan and capture jobs share the same collection/budget settings and source revision.
`operations.run_source` now validates policy and budget BEFORE Hub operations; the
CLI validates its budget before constructing the remote adapter.

## Qualification and external boundary

The local environment was rebuilt from hash-verified hosted artifacts, including
an actual Python 3.14.6 base interpreter and the existing locked dependency set.
The temporary read-only snapshot workflow is removed from the final tree. No
compatibility override, dependency edit or new diagnostic suppression was needed.
Local receipts identify their source baseline and changed-file identities; normal
PR checks and actual main/publisher outcomes must be observed separately.

The connected edithatogo HF OAuth scopes were inspected: repository reads only,
with no repository write permission. All four planned datasets returned not found.
The latest earlier trusted-main publisher recorded a missing HF_TOKEN. Nothing in
this adapter creates credentials or converts a blocked publication into success.

`pyproject.toml`, `uv.lock`, raw source metadata/PDFs, the AU/NZ acquisition
collections and 95% combined coverage/strictness gates remain unchanged. SourceRight,
CiteWeft and Authentext native qualification remains open; this adapter does not
claim those integrations executed. Every staged package keeps Gate B false. Bronze
corpus qualification must still precede Silver, Gold and Platinum production.
