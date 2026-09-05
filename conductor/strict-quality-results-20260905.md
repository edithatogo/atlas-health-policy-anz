# Strict-quality implementation: observed checkpoint

Existing tracks **T00/T06/T07**. Read after `strict-quality-20260905.md`; no new tracks.

The full added toolchain is resolved and committed. Hosted run `33962142453` passed the strict serial and parallel suites (279 tests each), resource-lifetime regressions, benchmark assertions, context validation and build on Python 3.14.6. It committed the verified safe normalization as `cd4d184d80ca721feb3c97bfa2c0893fab2d370b`. Exact receipts: `quality/resolved-test-tools.json`, `quality/normalization-result.json`, and the run's JUnit/diagnostic artifacts.

Warnings-as-errors detected genuine unclosed HTTPError responses at both acquisition boundaries. Both now close the response before propagation/disposition. Tests assert resource closure for permanent and retryable errors. The deliberate socket-denial test asserts the plugin's expected warning and exception without weakening global warnings-as-errors.

Subprocess coverage aliases map zipapp paths to the corresponding source instead of hiding files or ignoring parser warnings. Combined coverage is 97.63%, statement-only 98.66%, branch-only 94.46%. Do not call the last number a 95% branch-only pass.

**Strict configuration/enforcement is implemented; whole-repository static compliance is not complete.** At normalization, Ruff found 1102 diagnostics, basedpyright 1585 errors and ty 107 diagnostics. Formatting passed. Later small typing/namespace cleanups do not establish a blanket pass. The separate Strict Python Quality workflow remains failing for unresolved errors; there is no baseline exemption or continue-on-error.

Remaining bounded remediation: validate and type JSON/provenance records at their boundaries; replace untyped callback/mock/CLI signatures with concrete types or tested protocols; remove genuine unused/unbound paths; split excessive-complexity routines without changing acceptance gates; document public APIs and review narrow security exceptions. Retain real branch-specific diagnostics as the work queue, not as an acceptance baseline.

The PR remains draft. The earlier all-green ANZ checkpoint applies only to its original four workflows at its recorded commit, not the newly enforced strict checks. Full security and testing checks must be read at the new head. Scheduled mutation/prerelease jobs are configured but not claimed executed by this normalization run. No HF writes, original captures or Bronze/Silver/Gold/Platinum promotions occurred.

## Follow-up remediation

See `conductor/strict-remediation-20260905.md` and
`quality/strict-remediation-local.json` for the subsequent locally passing
repair. The counts above remain historical, not current-head diagnostics.
