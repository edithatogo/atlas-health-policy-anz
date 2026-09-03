# T01 — Source census, rights and Hugging Face contracts


## Objective
Build a closed, versioned census of Australian state/territory health PPG source surfaces and the rights/publication contract for the public Bronze data plane.

## Must requirements
- Enumerate official state/territory health policy repositories, document libraries, directives/standards/guidelines and relevant national comparator sources.
- Define source taxonomy, authority hierarchy, discovery/capture adapters and source health fields.
- Every discovered v1 item receives a disposition: captured, unchanged, superseded, unavailable, withdrawn, restricted/rights-unresolved, corrupt, retryable, duplicate or out-of-scope.
- SourceRight-compatible rights evidence distinguishes access from redistribution permission.
- Define public Hugging Face Bronze package structure, dataset card, per-object rights state, hashes and remote verification contract.
- Register source update frequencies and change-detection mechanisms where available.

## Non-compensatory gates
- Unknown census disposition -> fail closure.
- Redistribution without positive rights qualification -> publication blocked.
- Source authority/status/date ambiguity may be retained but must be explicit; it cannot be silently normalized.
