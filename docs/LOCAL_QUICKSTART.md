# Local and sensitive comparison quickstart

The portable runner is designed so that local deployment does not require
reimplementing the Atlas workflow. Sensitive documents remain on the local
machine. A public Gold/Platinum snapshot can be downloaded in advance and
pinned by SHA-256.

## Minimum deterministic path

Requirements:

- a compatible Python interpreter (portable deterministic core tested here on Python 3.13.5; production package contract remains Python 3.14.6);
- one local policy/document; and
- one pinned public Gold JSONL baseline.

No network connection or local model is required for the conservative baseline.

```console
python au-health-policy-atlas.pyz prepare-local local-policy.txt \
  --source-id local.policy.001 \
  --output-dir out/prepared

python au-health-policy-atlas.pyz institutional-gap \
  local-policy.txt public-gold.jsonl \
  --source-id local.policy.001 \
  --output-dir out/gap
```

The result includes a local preparation receipt, conservative Gold candidates,
a gap matrix, exact input hashes and `network_used: false`. Lexical baseline
matches remain candidate-level findings and are never silently promoted to
semantic equivalence.

## Offline bundle

A baseline, model manifest, framework package and other local inputs can be
assembled into a fixity-checked bundle before transfer to a disconnected PC:

```console
python au-health-policy-atlas.pyz bundle-build \
  --bundle-id hospital-gap-2026-09 \
  --output-dir offline-bundle \
  public-gold.jsonl model-manifest.json frameworks.json

python au-health-policy-atlas.pyz bundle-verify offline-bundle
```

## Optional local model

A qualified llama.cpp-compatible model can later be added for tasks whose
benchmark route requires semantic inference. The Atlas runner owns state and
routing; the model receives only bounded microtask packets and must return
schema-constrained output. The model endpoint is restricted to loopback.

The deterministic path remains available if the model is absent, fails, or
abstains. A weak model result changes the evidence state rather than blocking
completion of unrelated findings.

## Optional local NLP and GraphRAG

If spaCy is installed, prepare a sensitive/local policy with exact-offset NLP
features and a rebuildable private graph without network use:

```console
au-health-policy-atlas prepare-local local-policy.docx \
  --source-id local.policy \
  --output-dir build/local-policy \
  --spacy --graph
```

Query the local derived graph:

```console
au-health-policy-atlas graph-query build/local-policy/graph \
  "clinical deterioration escalation"
```

The graph and spaCy outputs are derived local artefacts. They do not upgrade
Gold/Platinum evidence and are not uploaded by the local workflow.

## Direction, limitations and confidence

`gap-matrix.jsonl` enumerates each reference requirement against local candidates.
`local-to-reference-candidates.jsonl` separately reports the reverse direction.
The receipt records the direction and reference denominator. An absent local
candidate is a retrieval observation requiring verification, not confirmed
non-compliance. Candidate confidence cannot exceed the weaker input assertion.
The conservative regex extractor is A2, not a semantic A0 authority.

The runner makes no deliberate network calls on this deterministic path.
For sensitive use, enforce network denial in the deployment and inspect host
logging/model settings; a `network_used: false` receipt is not a sandbox proof.
No qualified public Gold/Platinum snapshot has been published by this project yet.
Use synthetic fixtures for software trials and label them explicitly.
