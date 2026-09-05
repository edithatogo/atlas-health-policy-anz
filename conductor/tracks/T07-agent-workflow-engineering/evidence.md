# T07 implementation evidence

Initial executable bootstrap recorded 2026-09-03.

- 103 deterministic unit/integration/assurance tests pass in the available Python 3.13 host, with 96.61% branch-aware package coverage using `PYTHONPATH=src pytest -q -c /dev/null tests --cov=australian_health_policy_atlas --cov-branch`.
- `scripts/validate_context.py` passes after adding the executable contracts.
- `scripts/benchmark_modality.py` passes the initial five-case adversarial modality fixture at 100%, including `must not` precedence and explicit ambiguity.
- The portable zipapp executes deterministic modality classification and local document preparation without package installation.
- Local document preparation emits `network_used: false` and content identities.
- The institutional reference runner produces a local gap matrix against a pinned Gold JSONL fixture.

This evidence qualifies the software bootstrap only. It does not qualify live Bronze, Silver, Gold or Platinum corpus releases, parser/model performance on the production corpus, or external Hugging Face publication.

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
