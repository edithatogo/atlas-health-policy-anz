# Australian Health Policy Atlas

Evidence-first computational comparison of Australian state and territory
health policies, procedures and guidelines. This is a development repository,
not a qualified national policy corpus or clinical decision service.

## Current implementation boundary

The public source-surface census contains 28 official entry points covering
all eight states and territories plus Commonwealth comparators. A surface
census is not a document census. No original government payload or public
Hugging Face release was acquired in the latest execution environment.

The code includes bounded resumable capture, content-addressed storage,
public Hugging Face staging with anonymous byte verification, conservative
local comparison, derived GraphRAG, optional spaCy features, and a portable
Python runner. Production releases remain **Bronze → Silver → Gold → Platinum**.
Decision products sit above Platinum; they are not a fifth medallion layer.

**Artifact recovery, 5 September 2026:** the supplied `improved.zip` was an
empty 22-byte archive, and its qualification receipt reported failure.
Development resumed from the intact Git history at `a15c911`. Claims of later
features were not accepted without code. The delivery builder now reopens the
ZIP, verifies Git history and the expected commit, and checks portable-build
reproducibility before exposing deliverables. See
[implementation status](docs/IMPLEMENTATION_STATUS.md) and
[recovery evidence](evidence/engineering/recovery-20260905/input-audit.json).

## Use the deterministic local runner

From a checkout with an appropriate Python environment:

```console
PYTHONPATH=src python scripts/build_zipapp.py
python dist/au-health-policy-atlas.pyz doctor
python dist/au-health-policy-atlas.pyz classify-modality "The service must not disclose the record."
```

For institutional comparison, the primary matrix enumerates **reference
requirements against local candidates**, so a missing local clause is not
silently omitted. The reverse view is also written. Results are retrieval
candidates, not certified equivalence, compliance or non-compliance. See the
[local quickstart](docs/LOCAL_QUICKSTART.md).

## Public remote-first capture

```console
PYTHONPATH=src python -m australian_health_policy_atlas.operations --matrix
```

Capture uses governed scope, exact host allowlists, bounded target/link/depth
budgets, durable checkpoints and source-specific dispositions. Immutable HF
staging packages are independently downloaded and rehashed before their index
is advanced. Restricted, missing and incomplete sources remain visible.

Publication requires an actual HF write credential and a qualified locked
runtime; it does not repeatedly request redistribution approval. The configured
Actions workflow is not yet deployed or verified on a hosted runner. See
[remote staging and handoff](docs/RECOVERY_AND_REMOTE_STAGING.md).

## Architecture and governance

`archive-govt-nz` supplies preservation patterns; `global-medicines-atlas`
supplies comparative-evidence patterns; `rcagent` supplies portable-skill
patterns. SourceRight, CiteWeft and Authentext identities are pinned in
`.context/`; their native integration qualification remains open.

Conductor owns plans and evidence. Deterministic code owns execution state;
small models receive one bounded, source-grounded microtask. Lexical similarity,
graph proximity, model agreement and repeated rules are not proofs of equivalence.
Independent methods, calibration, extraction benchmarks and substantive
frameworks remain a qualification programme, not an implemented guarantee.

## Validation and distribution

The production contract remains Python 3.14.6 with uv 0.11.29 and a committed
lockfile. The current sandbox only supports a Python 3.13 compatibility run.
Latest measured results and unrun checks are recorded in the dated engineering
receipts; they must not be read as hosted CI or production qualification.

```console
PYTHONPATH=src python scripts/validate_context.py
# After committing a clean tree:
PYTHONPATH=src python scripts/build_delivery.py --output-dir dist/delivery
```

The delivery contains full Git history, a tested portable runner, and checksum
receipts. Raw corpus objects are not committed to this code repository.
