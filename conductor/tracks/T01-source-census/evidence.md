# T01 Evidence — Source Census v1

## Closed scope

Source Census v1 is a finite census of **official public source surfaces**, observed 3 September 2026. It intentionally does not claim that every individual policy, procedure, guideline or supporting attachment has already been downloaded; that is the Bronze v1 capture obligation.

The source registry contains 28 source surfaces covering Queensland, New South Wales, Victoria, South Australia, Western Australia, Tasmania, the Australian Capital Territory and Northern Territory, plus Commonwealth ACSQHC clinical-governance comparators. Each source has a jurisdiction, publisher/authority, URL, document classes, capture adapter, update mechanism, disposition and scope note.

Tasmania and the Northern Territory are represented as distributed-corpus jurisdictions rather than being forced into a fictitious central-register model. A previously inferred Tasmanian Chief Psychiatrist page was removed from the v1 registry and replaced with a verified public THS system-governance source.

## Hugging Face contract

The public Bronze target remains `edithatogo/au-health-policy-atlas-bronze`. `publication/huggingface/bronze-v1/` freezes the dataset-card and remote-verification contract. Remote publication itself is T02 evidence, not T01 evidence.

## Machine evidence

- `data/sources/source-surfaces-v1.json`
- `evidence/public-corpus/source-census-v1/completion.json`
- `evidence/public-corpus/source-census-v1/manifest.json`
- `publication/huggingface/bronze-v1/publication-contract.json`

The completion receipt records 28 surfaces, all eight state/territory jurisdictions, a national comparator, HTTPS endpoints, explicit dispositions and declared capture adapters.

## Limitations carried forward

Individual-document coverage, source-byte fixity, WARC/WACZ context, reconstruction and remote Hugging Face verification are deliberately not inferred from this census. They are non-compensatory T02 requirements.
