# Engineering evidence

## 5 September 2026 recovery and remote staging

Evidence: `evidence/engineering/recovery-20260905/`. The latest supplied improved
ZIP was empty and its summary said qualification failed; the intact baseline
was `a15c911`. The recovery pass implements and tests operational crawler,
remote staging, packaging and conservative candidate fixes. The latest measured
host test run is 222 passed, 97.59% combined line/branch-aware package coverage.
Exact commands and runtime deviations are in the machine receipt.

No original public payloads were captured; no HF dataset write, hosted CI run,
production lock resolution, or native external-tool execution occurred. This is
not closure of Bronze or any downstream production track. Future evidence must
bind the exact committed tree rather than rely on this narrative.
