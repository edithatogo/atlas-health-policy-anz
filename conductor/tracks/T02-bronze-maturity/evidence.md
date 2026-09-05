# T02 Evidence — Bronze v1 execution state

T02 is executing against the closed Source Census v1. A capture queue exists for all 28 source surfaces, with a focused nine-source clinical-governance vertical slice spanning every state/territory plus the 2026 national model.

## Implemented now

- source-specific capture queue and expected payload/receipt/fixity outputs;
- content-addressed Bronze/capture/publication software already in the executable Atlas core;
- public Hugging Face Bronze dataset-card/publication contract;
- post-upload immutable revision/byte/metadata verification code;
- shadow clinical-governance pipeline exercising downstream structures without crossing the Bronze gate.

## Current external blockers

The current model container has no outbound DNS/network path to the official source bytes. The connected Hugging Face integration exposes read/compute operations but no dataset-repository write operation. A minimal Hugging Face `cpu-basic` Job was attempted as a networked capture/publication bridge and returned HTTP 402 Payment Required.

Accordingly, no original-byte capture, fixity, recovery or remote Hugging Face publication is claimed. `evidence/public-corpus/bronze-v1/readiness.json` records Gate B as false.

This is an execution-environment blocker only: the networked capture and publication paths are already implemented and can run unchanged in GitHub Actions or another network/write-capable environment.

## Hugging Face execution receipt

- `evidence/public-corpus/bronze-v1/huggingface-attempt.json` records the authenticated connector identity, absent target datasets, lack of a dataset-write mutation, and the `cpu-basic` Jobs HTTP 402 result. It contains no credential material and explicitly records zero uploaded originals.

## 5 September 2026 recovery and remote staging

Evidence: `evidence/engineering/recovery-20260905/`. The latest supplied improved
ZIP was empty and its summary said qualification failed; the intact baseline
was `a15c911`. The recovery pass implements and tests operational crawler,
remote staging, packaging and conservative candidate fixes. The latest measured
host test run is 222 passed, 97.59% combined line/branch-aware package coverage.
Exact commands and runtime deviations are in the machine receipt.

No original public payloads were captured; no HF dataset write, hosted CI run,
production lock resolution, or native external-tool execution occurred. This is
not closure of Bronze or any downstream production track. Future evidence must
bind the exact committed tree rather than rely on this narrative.
