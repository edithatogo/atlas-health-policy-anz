# Agent Catalogue

These are target agents to be developed and benchmarked under T07. They are roles with contracts, not fictional reviewers and not claims of current implementation.

| Agent | Primary responsibility | Authoritative? |
|---|---|---|
| Census Agent | Enumerate official policy repositories/source sets and disposition every discovered item | No |
| Rights Agent | Apply SourceRight-compatible rights/redistribution checks and publication gates | No; human licensing gate remains |
| Capture Agent | Bounded acquisition, receipts, WARC/CAS/fixity and Bronze manifests | Mechanical evidence only |
| Bronze Auditor | Verify census completeness, fixity, provenance, recoverability and HF publication candidate | Gate evidence |
| Parser Ensemble Agent | Run qualified parsers, compare outputs and retain extraction-loss/disagreement records | No |
| Lineage Agent | Maintain page/DOM/cell/span lineage Bronze→Silver→Gold | Mechanical evidence |
| Assertion Extractor | Propose atomic actor/modality/action/object/condition/timeframe assertions | Candidate only |
| Assertion Verifier | Validate extracted fields against exact source spans and deterministic constraints | Qualification evidence |
| Equivalence Candidate Agent | Retrieve likely cross-jurisdiction equivalents using lexical/semantic/ontology signals | Candidate only |
| Equivalence Judge | Apply scope/authority/time/NLI/cross-encoder/LLM comparison contract | No; emits validity state |
| Framework Agent | Apply one versioned framework projection without contaminating other lenses | Derived analysis |
| Triangulation Agent | Compare independent method/model outputs and preserve agreement/disagreement | No majority-vote authority |
| Gap Analysis Agent | Construct reproducible gap matrices from qualified Gold/Platinum inputs | Derived analysis |
| Citation Agent | CiteWeft-compatible citation/source integrity | Quality evidence |
| Narrative Agent | Explain qualified tables without adding unsupported facts | Publication narrative only |
| Authentext Agent | Authentext/readability/humanization checks on narrative | Style only |
| Red-Team Agent | Search for source gaps, false equivalence, temporal/scope errors and unsupported claims | Adversarial quality |
| Reproduction Agent | Clean-room rebuild and comparison replay from pinned manifests | Verification evidence |

Every agent must expose typed inputs/outputs, abstention/failure states, model/tool manifests where applicable and tests against adversarial fixtures.
