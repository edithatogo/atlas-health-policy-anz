# Australian credentialing and model-SoCP metadata intake, 10 September 2026

This bounded work package belongs to T02. It adds public-source metadata and catalogue controls for credentialing and scope of clinical practice without claiming local adoption, complete binary preservation or medallion promotion.

## Scope

The collection request is stored at `data/source-intake/credentialing-socp-anz-20260910/request.json`. It covers the 2026 national credentialing guidance, the Queensland Health credentialing directive, the NSW State Scope of Clinical Practice Unit catalogue and eCredential implementation material, and Australian Medical Council Rural Generalist Medicine recognition.

## Implemented controls

- [x] Metadata-only publication boundary.
- [x] Explicit authority classes and source URLs.
- [x] Expected 88-entry model-SoCP catalogue structure.
- [x] Explicit distinction between 83 final entries and five entries under review after consultation.
- [x] Python 3.14 target recorded.
- [x] Evidence ceiling preventing catalogue metadata from being treated as local policy, service capability or an individual decision.
- [x] Deterministic unit tests for counts, category totals, source identity and fail-closed publication settings.
- [x] Collection design note describing Bronze–Silver–Gold–Platinum promotion rules and CHHHS adaptation gates.

## Remaining gates

- [ ] Capture and verify current official binaries where rights, access and publisher controls permit.
- [ ] Generate the full catalogue from current listing pages and compare it with the expected inventory.
- [ ] Record missing or changed document URLs as explicit source-health exceptions.
- [ ] Run SourceRight, CiteWeft and Authentext qualification in an approved execution environment.
- [ ] Publish a public-safe Hugging Face dataset only after repository-write authority and a dataset rights decision are available.

Repository metadata and tests do not establish source currency after the observation date, policy approval, implementation or operating effectiveness.
