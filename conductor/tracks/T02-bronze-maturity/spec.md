# T02 — Bronze Acquisition and Maturity

## Objective
Acquire, preserve, publicly publish and qualify the declared v1 source corpus before Silver production begins.

## Must requirements
- Bounded source-specific capture with original bytes, material HTTP context, observation time and capture receipt.
- Content-addressed storage with SHA-256 and optional BLAKE3.
- WARC/WACZ for web evidence where appropriate; original PDF/DOCX/HTML payload retained byte-for-byte.
- Provenance, source revision, authority/status metadata and explicit failure states.
- SourceRight-compatible source/provenance metadata without a repetitive redistribution approval step.
- Zero-loss/recoverability tests against the declared Bronze capture contract.
- Build and autonomously publish the public HF Bronze dataset when technical gates pass and credentials are available; verify remote immutable revision/bytes/metadata.
- Bronze maturity report closes the source census at a declared cutoff and scope.
- Emit a Bronze v1 completion receipt and immutable release manifest.

## Gate B
Silver production is blocked until Bronze v1 source census completeness, fixity, provenance, recovery and remote publication verification pass. Analytical uncertainty is not relevant to Bronze completion; missing required corpus objects or silent capture loss are.
