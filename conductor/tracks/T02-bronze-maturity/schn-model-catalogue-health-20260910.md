# NSW/SCHN model-SoCP catalogue source-health monitor

Status: repository implementation; public listing-page validation only

## Purpose

Maintain visibility of changes to the public NSW State Scope of Clinical Practice Unit catalogue without silently treating a changed web page, broken link or newly published model as an operative local requirement.

## Implemented

- read-only extraction of public PDF links from the medical/surgical, paediatric and dental listing pages;
- conservative specialty-to-link matching;
- explicit treatment of the five entries listed as under review after consultation;
- duplicate-link removal;
- failure on missing or ambiguous final-model links;
- source-page and category receipts;
- a machine-readable report with an evidence ceiling;
- synthetic unit tests; and
- weekly and manually dispatched Python 3.14 source-health workflow.

## Source-health response

A failed source-health run creates an investigation need, not an automatic catalogue amendment. The source steward should determine whether the cause is:

- publisher outage or access failure;
- page-layout change;
- renamed or replaced document;
- changed model status;
- a newly published or withdrawn model;
- a matching ambiguity; or
- an error in the reviewed local catalogue.

Any catalogue update requires preservation of the previous observation, a new observation date, source provenance, review and a distinct commit. CHHHS adoption remains a separate governance decision.

## Evidence ceiling

The monitor establishes the accessibility and apparent structure of public listing pages at a point in time. It does not establish document currency, legal or policy authority, permission to reuse, CHHHS adoption, facility capability, individual competence, scope or operating effectiveness.
