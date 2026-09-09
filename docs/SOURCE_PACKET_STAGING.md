# Verified source packets in public Bronze staging

This T02/T07 work package connects **already captured public originals** to the
existing public Hugging Face `HubStore`. It does not recapture sources, construct
crawl state, parse policies, qualify native ecosystem tools or close Bronze v1.

## Inputs and trust boundary

`data/sources/source-packets-v1.json` is a reviewed allowlist, not a source census.
Each entry pins a packet directory, the Git revision containing the originals,
independent SHA-256 values for its request and capture manifest, permitted HTTPS
source hosts, and unresolved census gaps. Registry changes require ordinary code
review/checks, not repeated approvals of each verified source. An unchanged input
must reproduce the same package bytes and content identity.

The first integration reuses the Queensland packet introduced by PR #10. Its
15 explicitly requested sources have eight captured PDFs (17,390,153 unique
bytes), seven recorded failures and a separate unresolved full-report URL. These
counts describe this packet only. They are not added to the frozen AU-v1 census,
220 ANZ acquisition profiles or authority-directory denominators.

Verification compares request membership with every outcome, checks original
metadata and exact bytes, rejects unexpected original files, and retains failure
reasons. It accepts only canonical safe paths and declared hosts. It checks the
PDF transport signature/end marker, not document validity, safety, reading order,
currency or applicability. It performs no OCR, semantic extraction or network
access. Source observations and notices remain unchanged; no new rights-approval
gate is introduced.

## Executable interface

From an installed locked environment:

```console
uv run --no-sync python -m scripts.source_packets verify
uv run --no-sync python -m scripts.source_packets stage --workspace /tmp/atlas-stage
uv run --no-sync python -m scripts.source_packets publish --workspace /tmp/atlas-publish
```

Verify/stage need only Python 3.14 and the source checkout. For dependency-free
checks use `PYTHONPATH=src python -S -m scripts.source_packets verify`. Publication
requires the existing locked `publication` dependency group and scoped `HF_TOKEN`
through environment/secrets. No credential is accepted as a command argument,
emitted in a receipt, or copied into a package. `--packet-id` selects one registered
entry, never an arbitrary institutional document.

`--receipt` selects the atomic progress journal. `--summary` optionally selects a
fixed-label Markdown status report; Actions passes its own step-summary path.
Keep both reports outside the staging workspace and preserved input locations.
A valid existing stage is independently reverified on a rerun. A corrupt stage,
unexpected member, overlapping or symlinked path fails instead of being overwritten.
Old receipts are not trusted to skip validation. This is re-execution with verified
stage reuse, not a general restart-from-journal engine.

## Immutable package and clean replay

Only independently verified members are staged:

```text
manifest.json
records.jsonl
evidence/request.json
evidence/capture-manifest.json
objects/<original-sha256>.pdf
```

Adjacent scripts, evaluation documents, models, embeddings and traces are never
selected. Identical original bytes are stored once while each source retains its
own record. The manifest binds the complete inventory and unresolved capture/census
observations. Runtime verification recomputes that manifest from pinned metadata
and actual originals: a re-sealed forgery cannot remove failures or promote Gate B.

The immutable public destination is:

```text
edithatogo/au-health-policy-atlas-bronze
  staging/packets/<packet-id>/<manifest-sha256>/...
```

Conditional Hub commits are followed by anonymous reconstruction at the exact
returned revision. Identical remote packages are verified again without rewriting
their paths. Conflicting or corrupt packages fail; no mutable latest pointer is
published. A concurrent unrelated writer may cause a conditional failure; a later
run can reverify without overwriting mismatched immutable data.

`restore_packet_stage(hub, spec, reference, destination)` is the independently
usable verifier. Supply both a successful publication reference and independently
trusted registry specification. The existing SDK downloader spools remote files
before caller-side size checks; this is not an OS sandbox or adversarial network
transfer quota. Fixity does not certify clinical or legal policy interpretation.

## Per-packet execution and failure semantics

Run receipts use schema version `1.1`; immutable package/reference schemas and
identities are unchanged. Every selected packet remains in the progress denominator,
including queued, failed and credential-blocked items. Checkpoints before and after
phase transitions preserve earlier observations and verified publication references
when a later packet fails. Snapshot data are detached from future mutations.

- `verified`: the requested verify/stage/publish operation completed. Use the
  publication fields to determine whether remote work was requested and verified.
- `blocked_missing_hf_token`: offline integrity/staging completed but no Hub adapter
  was invoked for publication. A green blocked job is not an upload.
- `partial_failure` or `failed`: at least one selected packet failed; the command
  exits nonzero. Independent packets still run, and successful references remain.
- `executing`: the last persisted phase is not a completed run. Interruptions are
  not swallowed or converted into a passing terminal result.

`network_attempted` records entry into the publication boundary. If an exception or
interruption prevents verified reconstruction, `remote_write_state` stays unknown;
no zero-write assurance is inferred. `network_used` is null when only attempted,
unverified remote work exists. `remote_bytes_verified` describes completed
publication items only; `all_selected_packets_published` requires the full selection.
A verified existing package is not evidence of a new write.

A journal-write failure stops before further packet side effects and preserves the
last durable observation. JSON and Markdown outputs are individually atomic, not a
cross-file transaction. Host power loss or runner deletion can still remove local
checkpoints before Actions uploads them; this is not a remote transaction log.
Error messages, tokens, headers and arbitrary source text are never put into the
fixed-label status summary. The per-packet barrier catches ordinary exceptions as
failed results, not BaseException interruptions or checkpoint exceptions.

## Automation and publication blocker

PR verification is secret-free. Only trusted-main push/manual runs may publish.
Main run `34401751088` at `192c7e652fc4ddbf76c6400a700754f509f9808d` returned
`blocked_missing_hf_token`; its publication job had no available HF_TOKEN. Configure
a scoped HF write credential using the repository's Actions secret mechanism, then
run this workflow on main. Do not send the credential through chat, commits or PRs.
This observation does not establish current permissions of another HF connection.

Actions retains only receipts, not raw originals. Existing Git-held public originals
are not deleted before verified HF storage exists. Every package/reference remains
`not_medallion_release: true`, `gate_b_passed: false`. Native ecosystem audits,
complete document acquisition and final Bronze release qualification remain separate.
