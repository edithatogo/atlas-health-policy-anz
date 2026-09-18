# Metro North credentialing comparator upload — 18 September 2026

## Intake

Two user-supplied ZIP bundles were received and inspected:

- `memo-medical-stars-30112021(1).zip`: 11 PDF documents concerning STARS / Metro North credentialing, including a Lower GI Endoscopy SoCP memorandum.
- `socp-clin-pharm.zip`: 38 PDF documents comprising Metro North scope-of-clinical-practice modules and the 2017 Scope of Clinical Practice List Project interim principles and definitions.

Total: **49 PDFs**.

`inventory.csv` records filename, byte length, page count, SHA-256 digest and embedded PDF title for every document.

## Intended use

These documents are comparator and historical-source material for the CHHHS credentialing and scope-of-clinical-practice project. They must not be treated as current CHHHS authority or automatically as current Metro North policy.

They are particularly relevant to:

- model-SoCP structure and granularity;
- facility and service overlays;
- specialised scopes;
- credentialing portability / cross-facility practice;
- STARS implementation and governance;
- comparison with SCHN model SoCPs and current national guidance; and
- development of proportionate CHHHS model scopes.

## Binary preservation status

The original uploaded ZIPs and extracted PDFs were SHA-256 inventoried during intake. The GitHub connector available for this ingestion can write UTF-8 repository files but does not accept a local binary file reference for bulk PDF upload. Therefore this commit records the complete fixity inventory and intake context; it does **not** claim that the 49 PDF binaries have been persisted in GitHub.

The binaries must be copied into the controlled source store / repository binary layer before this intake can be marked `binary_preserved=true`.

## Evidence boundary

Presence in this intake catalogue establishes only that the uploaded byte sequence was observed and hashed. Currency, authority, supersession, reuse rights and applicability require separate verification.
