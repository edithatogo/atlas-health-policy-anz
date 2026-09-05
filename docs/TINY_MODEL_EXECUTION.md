# Tiny-model execution contract

## Objective
The Atlas must remain executable by small/tiny local language models without relying on the model to remember the architecture, infer the next step, or recover from an oversized prompt. The orchestrator owns state, routing, evidence selection, validation and stopping. The model receives one bounded question at a time.

## Core design: compile context, do not dump context
Conductor is the authoritative project memory, but an execution model should not receive the whole Conductor corpus. A deterministic compiler produces a **microtask packet** from the active skill, work item and source evidence.

Each packet contains only:
1. one task identifier and one open question;
2. the exact skill/method selected by code;
3. permitted evidence spans and hashes;
4. non-negotiable invariants;
5. a compact output JSON Schema;
6. enumerated abstention/failure codes;
7. explicit stop conditions.

The model is therefore asked to fill a bounded typed slot, not to manage a project.

## Program-owned finite-state machine
Workflow transitions are code, not prose. A typical assertion item is:

`queued -> evidence_ready -> candidate -> verified | supported | provisional | abstained | failed`

The model cannot invent another state or choose a later medallion stage. Every work item is checkpointed, resumable and content-addressed to its input hashes.

## Tiny-model routing ladder
Use the lowest-capability method that passes the benchmark:

1. deterministic rules / parsers / hashes;
2. lexical or structural classifier;
3. tiny local model for a single bounded extraction/classification;
4. small local model if the tiny model fails calibrated acceptance;
5. independent method/model triangulation for difficult cases;
6. larger model only after local context repair and lower-tier alternatives fail.

Escalation is triggered by measured failure, not model self-confidence.

## Structured generation
Canonical model-backed outputs must use constrained generation. Preferred order:
- inference engine native JSON Schema;
- `llama.cpp` JSON-schema/GBNF constrained output for local execution;
- XGrammar where an engine integration benefits from token-level JSON Schema/EBNF constraints.

Pydantic/JSON Schema validation follows decoding. Structural validity is necessary but not evidence validity: exact source spans, source hash, scope, authority and time are checked separately.

## Evidence packets
Do not ask a small model to retrieve and reason over a whole policy. Retrieval code provides a minimal evidence bundle with stable anchors. For pairwise comparison, the default packet contains only the two candidate clauses plus the minimum surrounding scope/definition context required to interpret them.

Context is expanded only after a reason-coded failure such as `definition_missing`, `scope_unclear`, `exception_reference_missing` or `cross_reference_needed`.

## Prompt shape
Instructions use stable imperative sections in the same order:
- TASK
- EVIDENCE
- RULES
- OUTPUT
- ABSTAIN WHEN

Avoid long narrative preambles, role-play, chains of nested exceptions, or asking the model to choose its own methodology. One positive and one adversarial example may be included only when benchmark evidence shows they improve the target model.

## Verification over self-reflection
Do not depend on "think again", confidence scores, or unrestricted self-critique. Prefer:
- exact span existence tests;
- deterministic field checks;
- metamorphic mutations;
- an independent verifier with a different failure mode;
- replay against frozen benchmark examples.

## Prompt/model optimization
Prompt wording is a versioned artefact. Later experiments may use benchmark-driven prompt compilers such as DSPy/GEPA, but an optimized prompt is promoted only if it improves held-out jurisdictional and temporal benchmarks without degrading critical error classes. The optimizer never sees the final hidden test set.

## Local model portability
The execution contract targets an OpenAI-compatible local endpoint where practical, allowing `llama.cpp` and other local engines to be swapped without changing policy logic. Model manifests record model repository, revision, quantization, context window, tokenizer/chat template, engine version, constrained-decoding mode and benchmark results.

## Tiny-model acceptance
There is no blanket parameter-count requirement. A model is qualified per task class. A sub-1B model may be acceptable for modality classification but not for scope-sensitive equivalence. The routing table stores the cheapest/smallest model that passes each task-specific threshold.
