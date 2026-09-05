# T01 — Source Census and Hugging Face Contracts

## Objective
Build a closed, versioned census of Australian state/territory health PPG source surfaces and freeze the public Bronze publication contract.

## Must requirements
- Enumerate official state/territory health policy repositories, document libraries, directives/standards/guidelines and relevant national comparator sources.
- Define source taxonomy, authority hierarchy, discovery/capture adapters and source-health fields.
- Every discovered v1 item receives a disposition: captured, unchanged, superseded, unavailable, withdrawn, corrupt, retryable, duplicate or out-of-scope.
- SourceRight-compatible metadata records source identity, provenance, authority/source quality and reproducible acquisition context; redistribution approval is not a workflow gate.
- Define public Hugging Face Bronze package structure, dataset card, per-object provenance, hashes and remote verification contract.
- Register source update frequencies and change-detection mechanisms where available.
- Freeze a declared observation time and scope for Source Census v1 so the work can close discretely.

## Completion gate
- Unknown census disposition -> fail closure.
- Source authority/status/date ambiguity may be retained but must be explicit; it cannot be silently normalized.
- T01 closes when the v1 census and capture/publication contracts are complete at the declared cutoff. Later discoveries become a subsequent census release rather than reopening v1.
