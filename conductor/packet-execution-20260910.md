# Packet execution reliability: 10 September 2026 (Australia/Brisbane)

Existing T02/T07 work package. No new track, source scope, dependency or medallion
promotion. PR #12 is merged at `192c7e652fc4ddbf76c6400a700754f509f9808d` after
all seven PR workflows passed at `607bc3dc629d8e909b527ea952e682746a2d69ed`.

## Observed publication blocker

Trusted-main run `34401751088`, publication job `102635115348`, ran the locked
Python 3.14.6 publisher and returned `blocked_missing_hf_token`. No HF token was
provided to that job. Its green result means the blocker was recorded, not that
anything was uploaded. Artifact `10123727788` contains the publication receipt;
GitHub recorded digest `663990c3d22324b08deb8fd03c3374515e3a259beb0190a71762d04ee9f047a2`.
This observation does not infer current permissions of unrelated HF connections.

## Bounded implementation

The original runner wrote its aggregate only after the entire selection. A later
packet exception could discard earlier verified publication references. The
replacement persists detached, self-hashed progress before and after every
packet phase and keeps the full selected denominator, including failed/queued
packets. Each caught packet failure remains a nonzero final result while unrelated
packets continue. KeyboardInterrupt/SystemExit are not swallowed. A failed durable
checkpoint stops further side effects rather than being classified as a source
failure or overwriting the last valid progress with an empty failure record.

Publication intent is recorded before constructing the Hub adapter. Until remote
reconstruction returns, remote effects remain unknown. A verified existing
package is not described as a new write. Individual verified references survive
later failures; `all_selected_packets_published` is separate from the legacy
`remote_bytes_verified` field, which concerns completed publication items only.

A rerun verifies any existing staging directory against independent registry pins
and exact bytes; it never overwrites a corrupt stage. This is not automatic reuse
of a trusted old run receipt: every source/stage and remote package is reverified.
The status summary contains only fixed labels and numeric counts, not arbitrary
source text, exception messages, paths, headers or credentials.

## Hosted implementation qualification

All seven PR workflows passed at code head
`edb77fce9a9509c90aa7bf7586b97878e2574fe8`, tested through GitHub merge revision
`cc7d0fe2318523f9912eb648e1515a1ef8f140c5`. The full suite reports 457 unique
passing tests: all 435 previous cases plus 22 new regression cases. Combined
statement/branch coverage is 97.56%, above the unchanged 95% minimum. The new
packet_progress module has 100% measured statement/branch coverage; this does not
imply universal full coverage of the repository or script entry points.

Ruff/format/basedpyright/ty, all seven Test-Goblin jobs, Context CI, Dependency
review, routine Testing Frontier and secret-free committed-original verification
passed. Security jobs actually ran full-history Gitleaks, actionlint, zizmor,
CodeQL, the locked vulnerability audit and SBOM generation successfully.

Evidence: `quality/packet-execution-hosted-20260910.json`. Its artifact digest is
reported by GitHub, not locally re-hashed. The execution container is unavailable;
no local test or artifact-verification claim is made. The evidence-only commit
and actual main merge receive their own checks; PR #13 records those later
observations rather than implying this receipt can self-qualify.

## Unchanged boundaries

Regression tests cover good/bad/good selections, unknown remote effects after a
simulated committed upload, idempotent re-verification, corrupt stages, process
interruptions, checkpoint write failures, output collisions and sanitized reports.

Source originals, packet pins, AU/NZ collections, `pyproject.toml`, `uv.lock` and all
95%/strict gates remain unchanged. Actual publication remains blocked until a
scoped HF write credential is available to trusted-main execution. No paid compute,
private upload, new capture or Silver/Gold/Platinum production is initiated here.
