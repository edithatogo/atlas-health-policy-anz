# Bounded capture bundles and nine-source access diagnostic

This T02/T07 increment permits a small live access diagnostic without requiring a
Hugging Face token. It does not bypass public-dataset publication or Bronze gates.
It reuses the existing crawler, stage verifier and HubStore rather than creating
another acquisition data format or a second canonical corpus.

## Portable source-stage transport

`capture_bundle.export_bundle(stage, archive, policy)` accepts an already verified
ordinary source stage, binds its exact governed policy identity and exports only
`manifest.json`, `state.json` and referenced content-addressed original bytes.
Members are sorted regular files, with a fixed timestamp and stored ZIP encoding.
Identical stages produce identical archive bytes. The archive and its members are
bounded to 2 MiB in total and at most 512 entries; no compression is accepted.
Existing outputs and outputs inside the source stage are rejected.

`restore_bundle(archive, reference, policy, destination)` requires an independently
trusted reference AND policy. It verifies the archive hash before opening it,
checks sizes, member types and canonical names, and rejects duplicate names,
symlinks, directories, encryption, compression and traversal. It reconstructs into
a temporary sibling and reruns the existing complete stage verifier before moving
the result into a new destination. An invalid replay never installs a partial
destination. It does not call ZIP extractall. Export also verifies a clean replay
before emitting its archive.

The reference binds archive hash/length, manifest hash, source ID, policy hash and
explicit non-release flags. Recalculating an archive hash or self-sealing modified
metadata does not override the independent stage and policy pins. Hashes are not
signatures; an attacker controlling both the reference and trust configuration is
outside this trust model. Verification does not establish that a source is genuine,
current, clinically appropriate or legally applicable. Export reads an existing
local stage using its ordinary verifier; the archive quota is not a universal
memory bound for arbitrary local-stage inputs. Filesystem operations assume a
single owner, not hostile concurrent modification or an operating-system sandbox.

A restored stage is accepted by the existing `publish_stage` interface, retaining
its conditional immutable-publication and anonymous-reconstruction contracts. The
in-memory HubStore regression exercises that bridge; it is not a live HF upload.
No automatic cross-workflow artifact download is wired to a privileged publisher.

## Deliberately narrow AU/NZ diagnostic

The selection contains one existing entry for each of ACT, NSW, NT, QLD, SA, TAS,
VIC, WA and NZ. The NZ entry is the Ministry of Health publications surface. These
are seed access tests, not representative policy samples or document censuses.

Each derived policy has a separate `probe-` identity, a `bounded-seed-probe-v1`
version, depth zero, one target, one attempt, at most ten observed links and a
1 MiB captured-body limit. The nine original registry entries and their parent
policy hashes are retained. Existing `au-v1`, `nz-v1`, `authorities-v1` and `anz-v1`
collections are not changed. A closed probe cannot be confused with the original
source's full discovery checkpoint. The historical inventory cutoff is explicitly
not an actual retrieval timestamp; captured receipts retain real observation times.

```console
PYTHONPATH=src python -S -m australian_health_policy_atlas.seed_probe plan --output /tmp/probe-plan
PYTHONPATH=src python -S -m australian_health_policy_atlas.seed_probe run --output /tmp/probe-run
```

Use the declared Python 3.14.6 interpreter and fresh output paths. The plan needs
no site packages or network. Running the diagnostic intentionally accesses only
the selected public HTTPS seeds through the existing validated capture boundary.
The 9 MiB maximum concerns retained response bodies, not redirects, HTTP headers,
TLS traffic, billed runtime or a complete network-transfer budget. HTTP redirects
and source restrictions remain governed by the existing crawler.

`run.json` always names all nine selected IDs. After each completed source it
retains the access disposition and replay reference. An interrupt or unexpected
error leaves `execution_complete:false`; source access failures remain explicit
terminal crawl states. A completed diagnostic with failures is not a fully
captured selection. A 403/404/transport error never establishes absence of policy.
The current journal is local; runner deletion before retention can still lose it.

## Hosted workflow and finite artifact exception

`seed-probe.yml` compiles the plan on relevant PRs, without credentials or live
capture. Live diagnostics run only on trusted-main pushes affecting this code or
manual main execution. No new schedule is added. The workflow is read-only for
GitHub, has no HF credentials, and applies a 20-minute job timeout. It invokes no
model or paid compute job.

The small diagnostic capture artifact is retained for seven days, at most nine
2 MiB bundle files plus compact plans/references/receipts. This is an explicit
bounded exception to receipt-only Actions artifacts, not a new storage strategy.
Canonical, durable public datasets still belong on HF. Diagnostic artifacts may
expire or require GitHub access; they are not public HF dataset releases. Existing
packet and full-corpus acquisition workflows retain their original storage rules.

Every reference remains `not_medallion_release:true`, `gate_b_passed:false`.
Successful replay is fixity and state reconstruction, not a semantic comparison,
a native SourceRight/CiteWeft/Authentext audit, a policy-gap result or completion of
any medallion layer. Future durable publication requires separately verified HF
writes. Whole Conductor track states remain unchanged.

## Method references

- Python ZIP safety and format details: https://docs.python.org/3/library/zipfile.html
- Actions artifact digests and retention: https://docs.github.com/en/actions/tutorials/store-and-share-data
- HF immutable/conditional commit interfaces: https://huggingface.co/docs/huggingface_hub/guides/upload
