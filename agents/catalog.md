# Agent Catalogue

These are target agents to be developed and benchmarked under T07. They are roles with contracts, not fictional reviewers and not claims of current implementation.

| Agent | Primary responsibility | Autonomous authority |
|---|---|---|
| Census Agent | Enumerate official policy repositories/source sets and disposition every discovered item | May close mechanically supported census items; uncertainty is explicit |
| Source Provenance Agent | Apply SourceRight-compatible source identity, provenance and source-quality metadata | Mechanical evidence; no routine redistribution approval gate |
| Capture Agent | Bounded acquisition, receipts, WARC/CAS/fixity and Bronze manifests | Full for reversible acquisition/publication workflow |
| Bronze Auditor | Verify census completeness, fixity, provenance, recoverability and HF publication | May qualify Bronze when hard gates pass |
| Parser Ensemble Agent | Run qualified parsers, compare outputs and retain extraction-loss/disagreement records | May promote A0/A1 structural outputs; retain weaker outputs explicitly |
| Lineage Agent | Maintain page/DOM/cell/span lineage Bronze→Silver→Gold | Mechanical evidence |
| Assertion Extractor | Propose atomic actor/modality/action/object/condition/timeframe assertions | Candidate only |
| Assertion Verifier | Validate extracted fields against exact source spans and deterministic constraints | May promote qualified assertions according to A0–A4 contract |
| Equivalence Candidate Agent | Retrieve likely cross-jurisdiction equivalents using lexical/semantic/ontology signals | Candidate only |
| Equivalence Judge | Apply scope/authority/time/NLI/cross-encoder/LLM comparison contract | Emits evidence state; can autonomously promote A0/A1 only |
| Framework Agent | Apply one versioned framework projection without contaminating other lenses | Derived analysis with A0–A4 state |
| Triangulation Agent | Compare independent method/model outputs and preserve agreement/disagreement | May assign evidence state; no majority-vote authority |
| Confidence Agent | Compose provenance, coverage, comparability, benchmark and triangulation evidence into A0–A4 reason-coded state | Classification authority only; cannot override failed hard gates |
| Gap Analysis Agent | Construct reproducible gap matrices from qualified Gold/Platinum inputs | Full reporting, including clearly labelled A2/A3 findings |
| Citation Agent | CiteWeft-compatible citation/source integrity | Quality evidence |
| Narrative Agent | Explain qualified tables without adding unsupported facts | Publication narrative only; inherits finding evidence labels |
| Authentext Agent | Authentext/readability/humanization checks on narrative | Style only |
| Red-Team Agent | Search for source gaps, false equivalence, temporal/scope errors and unsupported claims | Adversarial quality; may downgrade but not invent evidence |
| Reproduction Agent | Clean-room rebuild and comparison replay from pinned manifests | Verification evidence |
| Release Closer Agent | Test finite release acceptance contract and issue completion receipt when satisfied | May close routine releases when all machine gates pass |

Every agent must expose typed inputs/outputs, abstention/failure states, model/tool manifests where applicable and tests against adversarial fixtures. Candidate-generating and validating roles remain separate.
| Packet Compiler Agent | Deterministically compile one open question, evidence subset, invariants, schema and stop rules | Mechanical only; cannot invoke a model or alter evidence |
| Task Router Agent | Select the smallest benchmark-qualified deterministic/model route from machine evidence | Mechanical routing; cannot upgrade evidence confidence |
| Local Runtime Adapter Agent | Execute a typed packet against a pinned local endpoint and return raw + parsed receipts | No network/file authority beyond runner contract |
| Trace/Replay Agent | Emit public reproducibility traces or local sensitive traces and verify replay identities | Evidence only; never publishes private traces implicitly |
