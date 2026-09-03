# T02 — Bronze acquisition and maturity


## Objective
Acquire and preserve the declared v1 source corpus and qualify Bronze to maturity before Silver production begins.

## Must requirements
- Bounded source-specific capture with original bytes, material HTTP context, observation time and capture receipt.
- Content-addressed storage with SHA-256 and optional BLAKE3.
- WARC/WACZ for web evidence where appropriate; original PDF/DOCX/HTML payload retained byte-for-byte.
- Provenance, source revision, rights state, authority/status metadata and failure states.
- Zero-loss/recoverability tests against the declared Bronze capture contract.
- Build rights-qualified public HF Bronze dataset candidate and, after explicit authorization, verify remote immutable revision/bytes/metadata.
- Bronze maturity report closes the source census at a declared cutoff and scope.

## Gate B
Silver production is blocked until Bronze v1 source census completeness, fixity, provenance, rights states, recovery and authorized remote publication verification pass.
