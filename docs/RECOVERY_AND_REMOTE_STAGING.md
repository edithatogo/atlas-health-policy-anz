# Recovery, remote staging and engineering handoff

## Known starting state

Development was recovered from the intact `a15c911` archive. The later supplied
improved ZIP was empty and had a failed qualification receipt. Do not use prior
conversational feature lists as executable state. Consult the actual Git tree,
`docs/IMPLEMENTATION_STATUS.md`, and dated machine receipts.

## Operating contract

The existing 28-surface inventory is frozen. `crawl-policies-v1.json` adds
initial bounded policies without rewriting that inventory. Its cutoff identifies
the inventory freeze, not the date when subsequently captured bytes existed.
Every HTTP observation records its own actual retrieval time. Changing a crawl
policy changes its hash and therefore its checkpoint identity; do not silently
reinterpret a previously closed scope.

A source run has a bounded queue. It records parent/depth, attempts, capture
receipts, permanent failures and explicit traversal boundaries. A reached depth,
link or target limit is not an exhaustive census. Unexpected external hosts are
recorded for source-adapter qualification, not silently followed. A source-specific
extension is required for public CDNs or document stores outside the seed host.

## Commands

Inspect planned jobs without a token or network request:

```console
PYTHONPATH=src python -m australian_health_policy_atlas.operations --matrix
```

Run one exact `source_id` from that matrix on a qualified networked checkout:

```console
# HF_TOKEN is supplied through the host's secret mechanism, never committed.
uv sync --python 3.14.6 --locked --no-default-groups --group publication
uv run --no-sync python -m australian_health_policy_atlas.operations   --source-id qld-policies-standards-root   --workspace build/source-run --request-budget 20
```

The example ID must be taken from the actual matrix; no command should guess a
source identifier. `--capture-only` deliberately bypasses publication for an
explicit local capture run. Without either that flag or HF_TOKEN, the runner
returns a machine-readable blocked result before starting network work.

## Durable publication protocol

1. Restore the source checkpoint from a pinned HF dataset revision and verify
   all files against its manifest before processing.
2. Capture at most the requested number of targets. Persist after every target;
   publish at bounded five-target intervals to limit interruption loss.
3. Validate the source package inventory, CAS objects, policy hash, state hash
   and exact readiness calculation.
4. Commit it beneath `staging/<source-id>/<manifest-sha>/` in the fixed public
   dataset `edithatogo/au-health-policy-atlas-bronze`.
5. Download every uploaded file anonymously from that exact returned revision
   into a clean temporary directory. Recalculate lengths and SHA-256 values.
6. Advance the policy-bound source pointer with conditional commit protection.
   Never roll back a newer generation or overwrite a conflicting source state.
7. Re-download the pointer. Report a verified staging receipt, not a medallion
   completion receipt.

A raw-byte upload and its pointer use distinct immutable commits. Cross-source
branch conflicts retry at most three times; same-source conflicts fail without
silently overwriting another run. A self-hash detects mutation, not an authorised
publisher's intent or clinical correctness.

The public dataset is not switched from private to public automatically. An
existing private target fails the public-only contract. Source objects are not
included in GitHub Actions artifacts; only operational receipts are uploaded.
Sensitive institutional inputs must never enter this public pipeline.

## Assessment is not final release closure

`scripts/assess_bronze.py` verifies the frozen census and all public source
packages at a pinned repository head. It returns `data_candidate_ready` and
explicit limitations. It always returns `gate_b_passed: false`: source adapter
completeness, final publication closure, preservation-context and independent
reconstruction qualifications are still required. No boolean or synthetic
fixture can stand in for these missing qualifications.

## Security and bounded autonomy

The capture implementation checks HTTPS schemes, authorities, ports, public DNS
answers and every redirect against the declared host set. These checks reduce
SSRF risk but do not eliminate DNS-rebinding/time-of-check races. Deployment
must enforce egress restrictions; neither a prompt nor the Python URL checker
is an operating-system sandbox. Bodies, queues, retries and batch sizes are
bounded. Raw/parsed policy text remains untrusted data, not agent instructions.

A missing credential generates one run-level blocked result. No repeated rights
approval is requested. No paid cloud job is launched automatically. Scope
boundaries and incomplete evidence are reported rather than silently relaxed.

## Toolchain and remaining platform steps

The inspected sandbox has Python 3.13.5, pytest 9.0.2 and no HF write token.
DNS requests for original payloads failed. The connected HF OAuth identity
has read-repos, not a repository-write scope. GitHub search returned no matching
Atlas repository; none was created or pushed by this pass.

The Actions definitions preserve Python 3.14.6, uv 0.11.29, pinned action SHAs,
least privilege and no persisted checkout credentials. Capture is disabled by
preflight until a committed production `uv.lock` and scoped write secret are
available. Workflow text and mocked SDK tests do not prove hosted execution.

SourceRight, CiteWeft and Authentext are pinned by identity. SourceRight is a
reference-verification boundary; CiteWeft is a neutral Rust extraction library,
not an invented command-line executable; Authentext changes presentation only
and must preserve evidence spans and normative language. Native installation,
interface qualification and integration receipts remain open.

## Verified delivery

Commit a clean tree, then run:

```console
PYTHONPATH=src python scripts/build_delivery.py --output-dir dist/delivery
```

The builder creates a fresh Git clone, packages it with history, rejects empty
or incomplete ZIPs, reopens and safely extracts the archive, verifies the exact
HEAD and `git fsck`, and confirms a clean restored tree. It builds the portable
runner twice and requires byte identity. Only then are final outputs copied
and checksum receipts written. No packaging result is labelled clinical,
production-corpus or hosted-CI qualification.
