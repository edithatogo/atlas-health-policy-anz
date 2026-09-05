# Reviewed Gitleaks finding: public dependency revision

The sole finding from full-history run 33958755168, job 101286754321, is the `authentext` value on line 7 of `evidence/engineering/recovery-20260905/dependency-observations.json` at commit `f6164295395bc5fe358eea462c6b469eb09dfddf`.

The value is public Git commit `ca39b86eb604a6fe4cfa9a0918638195af82c1af` in https://github.com/edithatogo/authentext, already recorded as a dependency revision. It is a 40-hex object ID, not an authentication secret. The historical file was read back through GitHub before this disposition. The generic-api-key heuristic matched the `authentext` key followed by high-entropy hexadecimal text.

`.gitleaksignore` exempts only this exact commit/path/rule/line fingerprint. No rule, path class, directory, history range or credential format is disabled. Every other finding continues to fail CI. The scanner still scans full Git history with redacted reporting.
