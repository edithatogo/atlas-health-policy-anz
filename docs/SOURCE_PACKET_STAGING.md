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

The verify and stage modes need only Python 3.14, the source checkout and its
originals. For dependency-free checks use `PYTHONPATH=src python -S -m
scripts.source_packets verify`. Publication requires the existing `publication`
dependency group and scoped `HF_TOKEN` through environment/secrets. No credentials
are accepted as command arguments, emitted in receipts or copied into packages.
Use fresh workspace directories: nonempty, overlapping and symlinked output paths
are rejected rather than overwritten.

The registry is the only source selector. Optional `--packet-id` selects one
registered entry, not an arbitrary local document. Metadata pins protect against
unnoticed input substitution, but hashes are not signatures and registry trust
still matters. This public uploader is not the sensitive institution-local mode.
It does not make an adversarial filesystem or malicious PDF safe.

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
own record. The manifest binds the complete inventory and includes the unresolved
capture/census observations. The staging schema is validated in contract tests;
runtime verification also recomputes the complete manifest from pinned metadata
and actual original bytes. A re-sealed forged manifest cannot remove failures or
promote Gate B.

The immutable public destination is:

```text
edithatogo/au-health-policy-atlas-bronze
  staging/packets/<packet-id>/<manifest-sha256>/...
```

The publisher uses conditional Hub commits and verifies the returned immutable
revision. It then downloads every declared member **anonymously** through the
existing Hub boundary and reconstructs the package in a clean temporary folder.
An existing identical package is reverified without rewriting its object paths.
A conflicting or corrupt package fails; no mutable latest pointer is published.
A concurrent unrelated writer may cause a conditional failure; a later normal run
can reverify/retry without overwriting a mismatched immutable package.

`restore_packet_stage(hub, spec, reference, destination)` is the same independently
usable Python verifier. Its `reference` comes from a successful publication
receipt; the caller must also supply the independently trusted registry `spec`.
Manifest origins, immutable revisions, member paths and declared budgets are
checked before downloads; each returned object is hash/size checked before use.
The existing Hub SDK downloader spools remote files before these checks, so this
interface does **not** claim OS-level isolation or an adversarial network-transfer
quota. Limits and exact object verification do not certify policy interpretation.

## Automation and evidence states

The `Original source packet integrity and public staging` workflow always verifies
registered packets in PR checks without secrets. Only trusted `main` push/manual
runs may invoke publication. Missing `HF_TOKEN` produces the explicit terminal
state `blocked_missing_hf_token`, no Hub calls, and a retained receipt. A green job
with that state means the blocker was recorded, **not** that publication passed.
Invalid data, authentication failures or failed remote fixity return nonzero with
a sanitized failure receipt. Uploaded Actions artifacts contain receipts only;
raw documents remain in their pre-existing Git source packet until independently
verified public HF storage is available. This work does not delete those originals.

Every package/reference carries `not_medallion_release: true` and
`gate_b_passed: false`. Even a fully captured finite packet cannot grant itself
production maturity. Software tests use synthetic fixtures and an injected Hub;
only a real successful publication run establishes a live HF revision. The
SourceRight/CiteWeft/Authentext native-qualification and final Bronze completion
contracts remain separate requirements.
