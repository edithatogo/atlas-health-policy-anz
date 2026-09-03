# T07 implementation evidence

Initial executable bootstrap recorded 2026-09-03.

- 90 deterministic unit/integration/assurance tests pass in the available Python 3.13 host, with 95.96% branch-aware package coverage using `PYTHONPATH=src pytest -q -c /dev/null tests --cov=australian_health_policy_atlas --cov-branch`.
- `scripts/validate_context.py` passes after adding the executable contracts.
- `scripts/benchmark_modality.py` passes the initial five-case adversarial modality fixture at 100%, including `must not` precedence and explicit ambiguity.
- The portable zipapp executes deterministic modality classification and local document preparation without package installation.
- Local document preparation emits `network_used: false` and content identities.
- The institutional reference runner produces a local gap matrix against a pinned Gold JSONL fixture.

This evidence qualifies the software bootstrap only. It does not qualify live Bronze, Silver, Gold or Platinum corpus releases, parser/model performance on the production corpus, or external Hugging Face publication.
