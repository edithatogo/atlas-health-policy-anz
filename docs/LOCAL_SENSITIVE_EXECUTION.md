# Local and sensitive-document execution

## Purpose
Institutional users may need to compare confidential, draft, commercially sensitive or otherwise non-public PPGs against public Atlas baselines without transmitting local source documents to the public service.

## Architectural pattern
Adopt the portable-core pattern demonstrated by `rcagent`: a self-contained Agent Skill describes the workflow, references and templates, while the host client controls execution, permissions, logging, model processing and data handling. The Atlas adds a stricter machine contract: the portable skill delegates state transitions and validation to the local runner rather than relying on a conversational agent to remember them.

A local package should therefore contain:

```text
skills/policy-gap-analysis/
  SKILL.md
  references/
    workflow.md
    method-selection.md
    evidence-states.md
    framework-selection.md
  assets/
    schemas/
    templates/
```

The `SKILL.md` is deliberately short. It selects one workflow/method and loads only the required reference, following the `rcagent` principle that adding a method must answer an articulated open question and that stop rules prevent "kitchen sink" analysis.

## Sensitive deployment modes
### Offline strict
- no network;
- pre-pinned public Atlas baseline and model artefacts;
- local `llama.cpp` or another qualified local endpoint;
- local DuckDB/Parquet;
- local embeddings/vector index if needed;
- traces and derived products remain local;
- network attempts fail closed.

### Connected private
- local confidential corpus never leaves the institution;
- only public Atlas releases/models may be fetched by pinned digest/revision;
- optional outbound update checks reveal no local text;
- publication/export disabled unless explicitly invoked by the local operator.

### Public
- normal Atlas mode using public policies and public HF artefacts.

## Privacy boundary
The public Gold/Platinum representation is a reusable baseline. Private documents are mapped locally into the same schema, then compared locally. No private document, chunk, embedding, trace, prompt or comparison result is required to be uploaded to GitHub or Hugging Face.

## Local agent runtime
A recommended compatibility target is an OpenAI-compatible local server such as `llama.cpp`. The runtime should expose only narrow tools: read pinned source spans, query local DuckDB, write typed work-item output, and request a bounded context expansion. Shell/network/file-system authority is not granted merely because the model requests it.

## Portable skill distribution
Later releases can ship a skills-only archive in the style of `rcagent`, with exact checksums, release receipts and compatibility evidence. Client-specific installers remain separate from the portable core. The same skill can be consumed by a coding-agent client or a purpose-built local runner, but compatibility is qualified per client/version rather than assumed.

## Trace discipline
Public runs may optionally emit a sanitised, source-public execution trace for reproducibility. Sensitive runs default to local traces only. Trace export is a separate operation and must never be an implicit consequence of analysis.
