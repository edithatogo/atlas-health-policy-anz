# Health Policy Atlas ANZ

Evidence-first computational comparison of Australian and New Zealand health policies, procedures, guidelines and their regulatory/standards context. Canonical repository: `edithatogo/atlas-health-policy-anz`. The Python package and planned public Hugging Face dataset identifiers retain their earlier `australian_health_policy_atlas` / `au-health-policy-atlas-*` names for compatibility.

This is a development system, not a qualified national corpus, legal-compliance service or clinical decision service.

## Current implementation

The recovered source and Git history are now hosted in this repository. CI-repair commit `c7dca11` passed Test-Goblin, Context CI, Dependency review and Security and Context, including real locked dependency auditing and SBOM generation. Python 3.14.6, uv 0.11.29 and the 95% coverage requirement are retained. Each later change needs its own hosted results; see the PR checks and dated Conductor evidence rather than inheriting a prior pass.

The code includes bounded resumable capture, content-addressed storage, public HF staging with anonymous byte verification, conservative local comparison, derived GraphRAG, optional spaCy features and a portable Python runner. Production release gates remain **Bronze → Silver → Gold → Platinum**. Decision products are derived outputs, not a fifth medallion layer.

## ANZ authority and policy sources

The original 28-surface Australian v1 inventory is frozen, covering all eight states/territories and Commonwealth comparators. It is a source-surface census, not an exhaustive document census.

The new typed catalogue contains **212 bodies/functions**. Nine named official directory snapshots have independently enumerated membership contracts. Open-ended categories have unknown denominators and an explicit remaining-scope ledger. Source registration does not establish document capture, legal applicability, statutory delegation, accreditation recognition or medallion maturity.

```console
PYTHONPATH=src python -m australian_health_policy_atlas.authorities
PYTHONPATH=src python -m australian_health_policy_atlas.authorities --sources nz-v1
PYTHONPATH=src python -m australian_health_policy_atlas.authorities --graph
PYTHONPATH=src python -m australian_health_policy_atlas.operations --collection anz-v1 --matrix
```

Collections: `au-v1` (28 profiles), `nz-v1` (81 NZ-selected profiles including joint bodies), `authorities-v1` (192 authority profiles) and `anz-v1` (220 combined profiles). Shared portals do not collapse separate issuing bodies. `NZ` is a national jurisdiction; `ANZ` is a shared-publisher retrieval scope, not a new legal jurisdiction. Regulators, professional standards setters, education accreditors, service accreditors, funders and policy owners have distinct roles.

The bounded capture workflow selects `anz-v1`. It persists source dispositions and stops honestly at crawl limits. Public HF publication requires an actual scoped write credential and verified locked environment; missing credentials do not imply publication. No live original-document capture, HF dataset creation or production release is claimed by this change.

See [the current ANZ checkpoint](conductor/anz-scope-20260905.md) for primary-directory references, scope limitations and execution boundaries.

## Local and sensitive comparison

```console
PYTHONPATH=src python scripts/build_zipapp.py
python dist/au-health-policy-atlas.pyz doctor
python dist/au-health-policy-atlas.pyz classify-modality "The service must not disclose the record."
```

The primary institutional matrix enumerates reference requirements against local candidates, so a missing local clause is not silently omitted. The reverse view is retained. Results are retrieval candidates, not certified equivalence or compliance. Sensitive documents remain local. See the [local quickstart](docs/LOCAL_QUICKSTART.md).

The portable zipapp includes the JSON/CSV source catalogues. An installed wheel outside a checkout can use the authority CLI's explicit `--directory` registry path; wheel-resource qualification remains separate from the tested portable route.

## Governance and validation

Conductor records requirements, finite work packages and evidence. Deterministic code owns execution state; small models receive bounded, source-grounded tasks. Lexical similarity, graph proximity, repeated rules and model agreement do not prove policy equivalence. Native SourceRight/CiteWeft/Authentext integration, extraction benchmarks and substantive framework qualification remain explicit work items.

`archive-govt-nz` is the preservation archetype, `global-medicines-atlas` the comparative-evidence archetype, `nlp-policy-nz` the intended NZ processing interoperability node, and `rcagent` the portable-skill archetype. Registration of these relationships is not native interoperability qualification.

```console
PYTHONPATH=src python scripts/validate_context.py
# From a clean committed checkout:
PYTHONPATH=src python scripts/build_delivery.py --output-dir dist/delivery
```

The recovery history is retained in [implementation status](docs/IMPLEMENTATION_STATUS.md) and [the input audit](evidence/engineering/recovery-20260905/input-audit.json). The delivery builder reopens archives and verifies Git identity and portable-build reproducibility. Raw corpus objects are not committed to this code repository.
