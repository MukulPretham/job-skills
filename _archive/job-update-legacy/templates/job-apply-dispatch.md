# Brief template — dispatching one `job-apply` run

Fill every `<>`. Delete nothing that is a rule; the child has no other context.

---

GOAL: submit exactly **<N>** verified applications on **<SITE>** for the user, then log
both in Notion and the local ledger. Report what was actually submitted.

READ FIRST (read_file): `<skill-dir>/SKILL.md`, `references/<site>.md`,
`references/candidate-profile.md`, `~/Desktop/resume.md` (source of truth for facts).

BROWSER — state the live transport explicitly, do not assume the skill's documented
one still runs. Say which is true:

- Raw CDP: `browser_cdp` against a tab id, `Page.navigate` to move, `Runtime.evaluate`
  to read the DOM, `element.click()` to click, `sleep 3-5` via terminal before reading.
  The tab is already signed in — verify with `Runtime.evaluate` before trusting it.
- Or the MCP session named `<session>` if that is what is live.

Never open more than 2 tabs. Never type credentials. A login page, CAPTCHA or 2FA
challenge: stop and report, do not attempt to bypass.

HARD RULES
- Fresher gate: skip anything stating a 2+ year minimum, senior/staff/lead, or a
  stack the resume does not support. `<0-2 yr / fresher / 1+ yr with freshers invited>`
  is eligible.
- Skip external-ATS postings unless this run explicitly allows them.
- Skip unpaid, bond/agreement-fee, training-fee and commission-only roles.
- **Already applied list** (frozen by the parent, do not re-derive):
  `<company — role; company — role; ...>`
- A click is not an application: count it only when the site's own confirmation
  surface says so. If you cannot verify it, report it as not submitted.

NOTION LOGGING — after each verified application, one at a time
- Parent `Job Applications` = `<parent_page_id>`; today (IST) = `<YYYY-MM-DD>`.
- Date page and `<SITE>` page (with the 7-column header) are pre-created:
  `<site_page_id>`. Append, never recreate.
- Row: `| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |`
  Status=`Applied`, Applied At=`YYYY-MM-DD HH:MM IST`, Link=`[View job](url)`.
- Ledger: `python3 <skill-dir>/scripts/ledger.py add --site <SITE> ...`

ARTIFACT (required)
Append one JSON line per verified application to
`~/.hermes/profiles/rex/cache/job-apply/<site>-<date>.jsonl`, including company, role,
url, salary, yoe, applied_at, and the confirmation text you actually saw.

REPORT
- each company + role + link + pay, and the exact confirmation surface per row
- skips, one line each with the reason
- Notion write result with the page id
- If you got fewer than <N>, say so and say why. Do not pad.
