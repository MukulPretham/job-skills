# Job Update — Changelog

Append a dated entry for every behavioural change.

## 2026-11-11

- **Learning rule made explicit:** every new Gmail selector, search behaviour, failure signature, evidence phrase, or status nuance must be written back into the corresponding `references/` file before the run ends, and a behavioural change goes into this changelog.
- Split the old combined job workflow into three skills: `job-find` (harvest and queue at `Drafted`), `job-apply` (submit the drafted queue), and `job-update` (sync statuses from Gmail).
- `job-update` now reads Gmail through the browser MCP in the user's already-signed-in browser, at `mukulpretham@gmail.com`. The legacy CDP/`gmail_lookup.py` path is archived under `_archive/job-update-legacy` and is not used by this skill.
- Watchlist statuses: `Applied`, `Applied*`, `Pending`, `In Progress`, `Viewed`, `Assessment`, `Interview`. `Drafted`, `Offer`, `Rejected`, and `Withdrawn` are skipped unless the user asks to re-check them.
- Only explicit evidence changes a row. "Application accepted for review" is not an offer. Digests and ATS auto-confirmations are not progress.
- Updates are status-only. `Applied At (IST)`, salary, YOE, and link are left byte-for-byte unchanged.
- Run Notes gets one section per sync, newest first, with checked / updated / unchanged / needs-human counts.
