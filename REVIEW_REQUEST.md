# PennyLab CSV Engineering — Independent External Review Requested

**Status: external review pending.** All recorded scores are internal assistant-authored tests, not external certifications or official pact0 trials.

## Frozen submissions
- `advanced_v1/`: original CSV join solution, original tests, original 100/100 report.
- `expert_v2/`: original SQLite-backed expert join solution, tests and 100/100 report.
- `expert_v3/`: subsequent corrected engine and 9-case holdout + 10-case regression tests. This is a **revision**, not a replacement for v2.
- `MANIFEST_SHA256.txt`: source-artifact fingerprints for comparison.

## Reviewer requested work
Independently test **advanced_v1** and **expert_v2** separately, then assess **expert_v3** as a revision. Please examine:
1. Many-to-many correctness and stable output ordering; duplicate keys and collisions.
2. CSV RFC-compatible quoting, embedded newlines, Unicode, BOMs and malformed rows.
3. Memory and runtime at scale; realistic resource usage and SQLite cleanup.
4. Atomicity, path validation, output destination handling, unexpected exceptions and partial writes.
5. Security under malformed or untrusted input; any injection or denial of service risk.
6. Clear differences between v2 and v3, and whether the fix introduces regression.

Please supply your own tests and run logs, findings per version, defects with reproducible fixtures, reviewer name/date, and a candid PASS/FAIL or conditional verdict. Voluntary review is unpaid and response is not guaranteed.

No personal datasets, credentials, payment methods, or account tokens are needed or included. These repositories and scores do not constitute marketplace certification.
