# Code scanning triage — 2026-09-06

Live GitHub CodeQL alert inventory was queried for `edithatogo/voiage` on 2026-09-06. The open alerts are recorded below with their current alert IDs and paths.

| Alert | Rule | Path | Disposition |
|---:|---|---|---|
| 1299 | `py/empty-except` | `packaging/spack-overlay/catalogue-license-sources/python.py:1022` | Imported Spack catalogue source. The empty handler is intentional best-effort metadata probing; no repository script callsite is affected. Preserve upstream source semantics. |
| 1298, 1297, 1296, 1294 | `py/polluting-import`, `py/mixed-returns` | `packaging/spack-overlay/catalogue-license-sources/{xsimd,python,openssl,expat}.py` | Imported Spack catalogue sources. These are upstream recipe compatibility conventions, outside the repository script surface requested for this repair; no safe local rewrite was made. |
| 1306, 1260, 1236, 1228, 1203, 1202, 1195, 1153 | `py/import-and-import-from` | tests and `voiage/cli.py` | The scientific-review test module now uses an explicit from-package module import. Three other cosmetic rewrites were withdrawn because those test bytes are frozen scientific evidence. Existing equivalent imports remain; no hosted alert dismissal is claimed. |
| 1278, 1277 | `py/ineffectual-statement` | `voiage/metamodels.py` | Required typing.Protocol method ellipses, not accidentally discarded calculations. Retained interface semantics; no runtime rewrite or alert dismissal. |

Alerts 1266 and 1259–1251, 1249–1244, 1243–1221, 1216–1204, 1201–1196, 1193–1168, and 1162–1142 are already `fixed` or `dismissed` in the live API response. The NLTK dependency has no vulnerable callsite in the assigned scripts and was intentionally not upgraded.

The retained repair changes only the import in tests/test_scientific_review_evidence.py. Three additional cosmetic rewrites triggered frozen-artifact digest failures and were withdrawn rather than rewriting historical scientific evidence. Required Protocol ellipses in voiage/metamodels.py and imported upstream Spack catalogue bytes are preserved. A fresh hosted scan must establish any resulting alert closure. No security gate is bypassed.
