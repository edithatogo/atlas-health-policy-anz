# Bounded Queensland policy-original intake, 9 September 2026

This is an additional, finite source-document work package within T02, not closure of T02 or amendment of the previously closed source census. The owner explicitly requested that public source documents themselves be sent into this repository. No institutional evaluation, model, assumptions, results, prompts or local project plans are in scope.

## Contract

Capture the 18 named government document URLs in `data/source-intake/qld-energy-resilience-20260909/request.json`, retaining unaltered original PDF bytes, SHA-256, source URL, timestamp, HTTP context, licence basis, attribution and a disposition for every request. Non-PDF challenge/error responses are failures, not documents. Each source has a 32 MiB limit; the collection has a 200 MiB limit. No crawl, no credentialed publisher access, no HF write, no extraction or medallion promotion.

The narrowly scoped Actions job reuses the existing native `capture_url` boundary. Original bodies are committed under `data/source-documents/qld-energy-resilience-20260909/`, not placed in Actions artifacts. Source integrity is checked again from the named remote Git revision before any completion claim. PDF magic/fixity checks do not certify semantic correctness or comprehensiveness. The original copyright notices remain intact; separate bibliographic metadata does not relicense logos or third-party works.

The same one-shot delivery job may export a Git bundle of the public Conductor dependency at the fixed owner-requested revision. This is public upstream dependency transport only, with no local evaluation upload.

## Planned acceptance checks

- [ ] Each requested source has a captured or explicit failure disposition.
- [ ] Original PDF bytes and receipt inventory are on the source-intake branch and independently re-downloaded/hash-verified.
- [ ] Only named source-intake/document and bounded workflow/work-package files changed.
- [ ] Public upstream dependency transport is verified separately; its absence cannot be hidden by document success.
- [ ] Release limitations are recorded; no whole-track or production medallion completion is claimed.

This document is a work-package scope, not evidence that any capture has yet succeeded.
