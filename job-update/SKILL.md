---
name: job-update
description: Sync the Status column of Notion -> Job Applications with evidence found in Mukul's Gmail (mukulpretham@gmail.com), using the user's already-logged-in browser. Use whenever the user says /job-update, "update my application status", "check my email for replies", "any interview or rejection", "sync Notion with Gmail", or asks whether applied or pending jobs have moved forward. Reads every site page, searches Gmail for each company and role, classifies only explicit evidence, updates the matching row, and verifies the write.
argument-hint: "[site]"
---

# Job Update

Refresh the **Status** column of the Notion *Job Applications* tracker from evidence in the user's Gmail. One run can cover every site page, or one named site.

This skill never applies to a job, never sends email, and never edits a row except its `Status` cell.

**Learning rule.** If a run discovers a new Gmail selector, search behaviour, failure signature, evidence phrase, or a status that the current vocabulary cannot represent, write it into the corresponding `references/` file before the run ends. Add a dated line to `references/CHANGELOG.md` for every behavioural change. A finding that stays only in the chat is lost.

## Read these first

| File | When | What it gives you |
|---|---|---|
| `references/gmail-playbook.md` | Every run | Gmail login check, search queries, row extraction, thread reading, failure signatures |
| `references/status-mapping.md` | Every run | The exact status vocabulary and the evidence required for each change |
| `references/notion-status.md` | Before writing | How to find the row, replace only the status cell, and verify |
| `references/CHANGELOG.md` | Every run | What changed recently; append your own change |
| `../job-apply/references/candidate-profile.md` | When a company name is ambiguous | Identity and standing facts, so you search the right name |

**Browser MCP.** This skill drives the user's real browser. On this machine the MCP is exposed as `browse`:

- `tools.browse.status()` for relay, extension, and connected browsers
- `tools.browse.session_new({ id: "gmail-update" })` for an isolated tab
- `tools.browse.execute({ code })` for Playwright: `page`, `context`, `snapshot()`, `ref()`, `handoff()`

If the harness exposes `browser-control` instead, use `tools["browser-control"].execute` with the same Playwright code. **Never add or configure an MCP server yourself.** If neither is present, stop and tell the user to add the `browser-control` MCP.

## Scope

Default: **all site pages** under `Job Applications`. If the user names a site (`/job-update wellfound`), do only that site.

Ask only if the request is genuinely ambiguous. "Update my applications" means all sites. "Check Wellfound replies" means Wellfound only.

## Preflight

1. **IST clock.** `python3 <skill-dir>/scripts/ist_now.py`, or `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M %Z'`. Use it for the Run Notes heading.
2. **Notion reachable.** `notion-search` for `Job Applications`; confirm the root answers. If Notion is down, stop and tell the user; there is nowhere to write the result.
3. **Browser health.** `tools.browse.status()`. Create or reuse a session named `gmail-update`.
4. **Gmail login check.** Open `https://mail.google.com/mail/u/0/#inbox` and wait for the inbox to render. Confirm:
   - The URL stays on `mail.google.com` (not `accounts.google.com`).
   - The account chip or avatar shows `mukulpretham@gmail.com`.
   - The page shows an inbox, not a `Sign in` button.

   If signed out, stop and say:

   > "You're signed out of Gmail. Please log in as mukulpretham@gmail.com in the browser, then tell me when you're done."

   Wait for confirmation and re-check. Never type a password, solve a CAPTCHA, or switch Google accounts yourself. If a different account is signed in, ask the user to switch; do not silently search the wrong mailbox.
5. **Open Notion and Gmail on separate tabs or in sequence.** Do not mix their DOM handles. Read Gmail in the `gmail-update` session; write Notion through the MCP.

## Build the watchlist

Fetch the root and enumerate the site pages. Ignore `Run Notes` and `Hyderabad Outreach`.

For each site page, parse every row shape:

- real table rows (`| ... |`)
- escaped paragraph rows (`\| ... \|` joined by `<br />`, currently Shine and Hirist)
- any dated second table, but label it separately in the report

Select rows whose Status is one of:

| Include | Meaning |
|---|---|
| `Applied` | Submitted, waiting |
| `Applied*` | Submitted with a footnote, waiting |
| `Pending` | Site shows the application as pending |
| `In Progress` | Under review |
| `Viewed` | Application opened |
| `Assessment` | Online test stage |
| `Interview` | Interview stage |

Skip `Drafted` (not submitted), `Offer`, `Rejected`, and `Withdrawn` (already terminal). If the user explicitly asks to re-check a terminal row, include it, and only change it when the new evidence is unambiguous.

Record for each row: site, exact original line, company, role, current status, applied-at, link, page id.

**Volume.** A full board can hold well over 100 applied rows. Process site by site. Start with the broad Gmail sweep (next section), then search individually only for the companies the sweep did not resolve.

## Gmail search strategy

Follow `references/gmail-playbook.md` for selectors and waits.

### Pass 1 — broad sweep

Open a Gmail search for the recent application mail:

```
newer_than:60d (application OR applied OR interview OR assessment OR offer OR rejected OR "next steps" OR "not moving forward")
```

Add an ATS pass for the common senders:

```
newer_than:60d from:(greenhouse OR lever OR workable OR ashbyhq OR smartrecruiters OR rippling OR workday OR icims OR successfactors)
```

Read the visible threads and match the sender, subject, and snippet to companies on the watchlist. This catches most updates in two searches.

### Pass 2 — per company

For every watchlist company still unresolved, search:

```
"<Company Name>" newer_than:60d
```

If the name is generic (`Build AI`, `Certa`, `Ema`, `SAP`), add `application` or the role:

```
"<Company Name>" ("<Role>" OR application) newer_than:60d
```

If the company name keeps failing, search by ATS sender plus the company or role.

### Reading

- Prefer the newest application-specific thread.
- Ignore job alerts, digests, "new jobs for you", and marketing mail that merely mentions the company.
- Snippets truncate around 150 characters. If the meaning depends on the hidden part, open the thread and read the body.
- Open at most one thread at a time. Return to the result list after reading.
- Do not reply, forward, archive, delete, label, or mark anything as spam. Read only.

## Classify honestly

The full table is in `references/status-mapping.md`. The short version:

| Evidence | New status |
|---|---|
| "Your application was viewed" / "opened your application" | `Viewed` |
| Online test, coding challenge, take-home, HackerRank, Codility, assessment link | `Assessment` |
| Interview invite, scheduling link, call request | `Interview` |
| Offer letter, "pleased to offer", "selected", "congratulations" with a role and next steps | `Offer` |
| "Unfortunately", "not moving forward", "other candidates", "decided not to proceed", "regret to inform" | `Rejected` |
| "Under review", "reviewing your application", "application received" | `In Progress` only if the row is not already `Applied` |
| Confirmation of submission only | no change |
| Newsletter, digest, job alert, recruiter sourcing mail for a different role | no change |

Rules:

- **Only explicit evidence changes a row.** A wrong rejection is worse than a stale status.
- Match on **company + role**, never company alone. Several companies have two rows.
- "Accepted" is not automatically an offer. "Your application was accepted for review" means `In Progress` at most. Only an offer or selection email means `Offer`.
- An Indeed auto-confirmation means nothing beyond `Applied`. Do not promote a row because a confirmation exists.
- Wellfound digests mention companies in the snippet. They are not updates.
- If a thread is ambiguous, leave the row alone and list it under "needs human" with the subject and date.
- Never downgrade an `Interview` or `Offer` row because an older rejection exists. Use the newest evidence and the current stage.

## Update the row

Follow `references/notion-status.md`.

- Change **only** the `Status` cell. Leave `Applied At (IST)`, salary, YOE, and link byte-for-byte identical.
- Fetch the site page fresh immediately before writing. Notion rewrites bare domains and escapes `_` and `$`.
- Use `notion-update-page` with `command: "update_content"`, `old_str` = the exact fetched row, `new_str` = the same row with the status cell replaced.
- For an escaped paragraph row, replace the exact escaped line fragment, not the whole page.
- Fetch again and confirm the new status is present. A successful API call is not proof.
- If more than one row matches company + role on that site, list the matches and ask which one. Do not guess.

**Batch the writes per page**, but verify each page before moving to the next. If a write fails, report the exact error and keep the old status.

## Run Notes

After the last update, append one section to `Job Applications -> Run Notes` (page `4113109c-a531-81a5-93b9-f1c654ae58c0`), newest first:

```
## YYYY-MM-DD — Gmail status sync

**Checked:** <n> applied or pending rows across <n> sites
**Updated:** <n>
**Unchanged:** <n>
**Needs human:** <n>

| Site | Company | Role | Old | New | Evidence (<= 12 words) |
| --- | --- | --- | --- | --- | --- |

**Needs human:** <company, role, subject, why ambiguous>
**Notes:** <anything the status column cannot hold>
```

Never put applications in Run Notes. It is a log, not a table of jobs.

## Reporting

Open with a plain status word so the user never has to ask whether it finished:

```
STARTED — checking <n> applied or pending rows across <n> sites
FINISHED — checked <n>, updated <n>, unchanged <n>, needs human <n>
```

Then:

```
| Site | Company | Role | Old | New | Evidence |
...

Needs human:
- <Company> / <Role>: <subject> — <why it is ambiguous>

Notion: Job Applications -> <site pages touched>
Run Notes: <url>
```

Keep it short. Counts, the changes that matter, and the items that need the user. Do not narrate the search process.

## When to stop early

- Gmail logs out, shows a CAPTCHA, or lands on a Google sign-in page. Hand off to the user.
- Gmail search starts returning empty pages repeatedly. Retry once, then report the affected rows as `unverified`, never as "no mail".
- Notion becomes unreachable. Stop writing, keep the findings in the report, and tell the user.
- The board is far shorter than its normal row count. Re-fetch before trusting it; a truncated page is not an empty one.

## Self-update protocol

This is mandatory, not optional.

1. Append a dated field note to `references/gmail-playbook.md` when Gmail's selectors, search behaviour, or failure modes change.
2. Add new evidence phrases to `references/status-mapping.md` when a real email introduces one.
3. Update `references/notion-status.md` when the row shapes or page layout change.
4. Never store email content, credentials, cookies, tokens, or unnecessary personal data in the skill. A status and a one-line reason are enough.
5. Append a dated entry to `references/CHANGELOG.md` for any behavioural change.

## Quick checklist

- [ ] Scope confirmed: all sites, or one named site
- [ ] IST date captured
- [ ] Notion root reachable
- [ ] Browser healthy; `gmail-update` session
- [ ] Gmail signed in as mukulpretham@gmail.com, or user handed off
- [ ] Watchlist built from `Applied`, `Applied*`, `Pending`, `In Progress`, `Viewed`, `Assessment`, `Interview`
- [ ] Broad Gmail sweep, then per-company searches
- [ ] Only explicit evidence used
- [ ] Company + role matched, not company alone
- [ ] Only the Status cell changed
- [ ] Every write verified by a fresh fetch
- [ ] Run Notes appended
- [ ] New findings written into `gmail-playbook.md` / `status-mapping.md` and `references/CHANGELOG.md`
- [ ] Report lists checked, updated, unchanged, needs-human
