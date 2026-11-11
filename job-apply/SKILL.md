---
name: job-apply
description: Apply to jobs that are already queued as Drafted rows in Notion -> Job Applications, one site per run, through the user's own logged-in browser. Use whenever the user says /job-apply, "apply to the drafted jobs", "apply on Indeed/Wellfound/Cutshort", "submit the queue", "auto-apply", or asks to turn drafted roles into applications. Checks the site login before touching a job, re-screens every live listing against the bundled resume, writes human-sounding answers under the locked style rules, verifies each submission on the site's own confirmation surface, and flips that Notion row from Drafted to Applied.
argument-hint: "[site] [quantity]"
---

# Job Apply

Apply to jobs that are already on the board as **`Drafted`**. This is a runner, not a researcher: it does not search for new roles (that is `job-find`), and it does not rewrite the resume.

**One site per run.** `/job-apply indeed` means Indeed only. Never open another job board in the same run unless the user explicitly asks for a multi-site batch, and even then run the sites one after another, not in parallel.

**90-second rule, hard floor.** On the same site, wait at least **90 seconds between applications**. Start the clock when the previous submission is verified. Do not open or start the next application on that site until the 90 seconds have passed. Use a real wait (`await page.waitForTimeout(90000)` or the remaining time if the verification itself took a while); never skip it, shorten it, or assume the site reference's shorter pacing overrides it. Different sites are not covered by this rule, but they still run sequentially.

**Learning rule (living documentation).** Append what you learn to the site reference's field notes and to the changelog after every run. If a run discovers a new selector, question type, login step, rate-limit response, external-ATS pattern, or status phrase, that finding must be written into the corresponding `references/` file before the run ends. A finding that stays only in the chat is lost.

**Tool name note.** The older site references were written against an MCP called `browser-control`. On this machine the same MCP is exposed as `browse`, so translate one-to-one: `tools["browser-control"].execute` becomes `tools.browse.execute`, and `session_use` / `session_new` / `status` are the same names on `browse`. The Playwright code inside `execute` is unchanged.

## Read these first

| File | When | What it gives you |
|---|---|---|
| `../job-find/resume/resume.md` (preferred) or `resume.md` (fallback) | Every run | The canonical resume markdown |
| `../job-find/resume/mukul_pretham_resume_v5.pdf` | Every run | The PDF to upload when a form asks for a file |
| `references/candidate-profile.md` | Every run | Resume facts, target roles, eligibility rules, standing answers |
| `references/answer-rules.md` | Before the first form | The locked answer style, character limits, and what never to invent |
| `references/drafted-queue.md` | Before reading Notion | How to read `Drafted` rows, flip them to `Applied`, and handle malformed rows |
| `references/notion-logging.md` | Before writing to Notion | Exact hierarchy, table format, MCP calls, verification |
| `references/indeed.md` | Site is Indeed | Exact apply flow, smart-apply modules, failure signatures |
| `references/wellfound.md` | Site is Wellfound | Exact dialog flow, duplicate/external rules |
| `references/hiringcafe.md` | Site is Hiring Cafe | Employer ATS flows: Ashby, Rippling, Workable, Lever, Greenhouse, SmartRecruiters |
| `references/cutshort.md` | Site is Cutshort | `/profile/*` URLs, questionnaire queue, irreversible submit |
| `references/new-site-template.md` | Site has no runbook | Recon protocol and the reference file to write |
| `references/CHANGELOG.md` | Every run | What changed recently; append your own change |

Re-read the site reference at the start of every run. Sites change their markup; memory of a previous run is not evidence about the live page.

**Resume bundle.** The resume lives in the sibling `job-find` skill so both skills share one copy:

```
../job-find/resume/resume.md
../job-find/resume/mukul_pretham_resume_v5.pdf
```

Read the `job-find` copy first. The local `resume.md` is only a fallback if the sibling skill is missing. If both are missing, stop and ask the user to supply it; do not apply from memory.

**Browser MCP.** This skill drives the user's real browser. On this machine the MCP is exposed as `browse`:

- `tools.browse.status()` for relay, extension, and connected browsers
- `tools.browse.session_new({ id: "<site>-apply" })` for an isolated tab
- `tools.browse.execute({ code })` for Playwright: `page`, `context`, `snapshot()`, `ref()`, `handoff()`
- `tools.browse.session_reset()` when finished

If the harness exposes `browser-control` instead, use `tools["browser-control"].execute` with the same Playwright code. **Never add or configure an MCP server yourself.** If neither is present, stop and tell the user to add the `browser-control` MCP.

## Ask before starting

The queue is the `Drafted` rows. Ask two things once, in one `question` call. The tool adds a free-text "Type your own answer" option automatically; keep it.

**Question 1 — site**

> "Which site's drafted queue should I work?"

Options: the site pages under `Job Applications` that currently have `Drafted` rows, plus `All sites with drafted rows` as the last option. Show the count in each label, for example `Wellfound (4 drafted)`.

**Question 2 — batch size**

> "How many applications should I submit in this run?"

Options: `All drafted`, `5`, `10`, `15`. The user may type any number.

If the invocation already supplied them (`/job-apply indeed 10`), use them. If it supplied one, ask the missing one.

If the user chooses `All sites with drafted rows`, treat it as an explicit sequential multi-site batch: finish one site completely, report it, then start the next. Never drive two sites at the same time.

If there are no `Drafted` rows on the chosen site, stop and say so. Offer to run `job-find` for that site; do not search for jobs in this skill.

If the chosen site has no runbook in `references/`, tell the user it is a new site and offer a read-only recon pass. Write `references/<site>.md` from `references/new-site-template.md` before submitting anything. Do not freestyle an unfamiliar apply flow.

## Preflight

Do these in order.

1. **IST clock.** `python3 <skill-dir>/scripts/ist_now.py`, or `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M %Z'`. Capture the exact time for the `Applied At` cell.
2. **Load context.** Read the resume markdown, `references/candidate-profile.md`, `references/answer-rules.md`, and the site reference. Keep them in context.
3. **Notion reachable.** `notion-search` for `Job Applications`; confirm the root answers. If Notion is down, tell the user before applying. They may prefer to fix it first.
4. **Browser health.** `tools.browse.status()`. Create or reuse a session named `<site>-apply`. If the relay says stopped, run a trivial execute to start it, then navigate.
5. **Login check.** Open the site and verify the signed-in surface in its reference. If the page shows Login / Sign up / Create account, stop and say:

   > "You're signed out of <site>. Please log in manually in the browser, then tell me when you're done."

   Wait for confirmation and re-check the rendered page. **Never type a password, create an account, or solve a CAPTCHA.** Use `handoff()` for an interactive challenge.
6. **Ledger.** `python3 <skill-dir>/scripts/ledger.py list --site "<Site>" --limit 20`. Keep recent company/role pairs in mind.

## Read the queue

Follow `references/drafted-queue.md`.

1. Fetch the chosen site page.
2. Parse every real table row and every escaped paragraph row.
3. Select rows whose Status is exactly `Drafted`.
4. Keep the row's exact original text; you will need it byte-for-byte for the status update.
5. De-duplicate by company + role and by normalised link. If two rows point at the same job, apply once and report the duplicate.
6. Build the **applied set** from every row on that site page, in every status, plus the ledger. A `Drafted` row is known but unsubmitted; an `Applied` row is already done. Run the ledger cross-site check once for any company that looks familiar.
7. Order: newest drafted first, then down the page.

A `Drafted` row is **not** an application. It only becomes one after a verified submission.

## Re-screen every drafting at apply time

A harvested row ages fast: the posting may be removed, newly unpaid, newly years-gated, or newly external. Open every link live before deciding.

**Hard skip, leave the row at `Drafted`:**

- Stated minimum of 2+ years anywhere, including a modal `Experience` bar or the body.
- Senior / staff / principal / lead / architect / manager / SDE II+.
- QA, SDET, manual testing, L1/L2 support, night-shift ops, data or business analyst.
- .NET-only, PHP-only, SAP/ABAP, Salesforce, or an unsupported stack.
- Unpaid internship, training-plus-placement fee, commission-only, bond with a fee.
- External ATS (`Apply on company site`, Workday, Greenhouse, Lever, SmartRecruiters, email-only) unless the user explicitly allowed it for this run. Hiring Cafe is the standing exception because it has no native apply form.
- Dead or removed listing, title/description mismatch, mass-produced low-quality ad.
- Already applied on the site. Do not resubmit. If the site shows a real application date, update the Notion row to `Applied` with that date and say so.

**Case by case:**

- `Fresher`, `0–2 years`, `entry level`, `graduate`, or no years stated with knowledge-based wording: eligible.
- `0–3` / `0–4 years`: eligible.
- `1+ years`: eligible only when the JD also invites freshers, interns, or strong projects. A mid-level-sounding JD is a skip.
- `1+ years` with Wellfound's soft `Improve your odds` warning: informational, not a skip. Only `2+` is a hard stop.
- Paid internship: eligible when the stipend is stated or clearly non-zero. Flag "contribution-based".
- Salary below ₹4 LPA: not an automatic skip. Unpaid is always a skip.

Every skip gets a one-line reason for the report.

## Answer rules (locked)

The full rules are in `references/answer-rules.md`. Read them before the first form. The non-negotiables:

1. **Write like a person, not a form.** First person, plain words, 2 to 3 sentences by default. Not one clipped line, not a paragraph.
2. **No `--`, no em dash (`—`), no en dash (`–`) as a separator, no hyphen used as a bullet or pause, no bullet lists, no emoji, no markdown, no headings.** Normal hyphenated words are hard to avoid, so prefer spelling them out in free text (`full stack`, `back end`).
3. **Respect a stated character or word limit.** If the field says 200 characters, stay at or under 200. Trim a sentence; never cut mid-word and never pad. If no limit is stated, aim for roughly 250 to 360 characters.
4. **Tailor to that job.** Read the JD first. Name one concrete thing the company does or builds, then tie it to one or two real resume facts. Never paste a generic answer.
5. **Never invent experience, skills, projects, salary, notice, or personal facts.** If a required fact is not in the resume or standing answers, park the job and ask the user in one batched message at the end.
6. **No "I am a fresher".** Say what you have built, not what you lack.
7. **Messages to recruiters** follow the same style: greet by first name, 2 or 3 sentences, say the thing, close by offering a call. No bullets, no corporate filler.
8. **Pay questions are the user's call.** Standing expected CTC is ₹4,00,000 per annum. If a form asks whether a specific posted band is acceptable and the band is below ₹4 LPA, stop and ask; do not auto-accept.

If a field is a plain factual input (name, email, phone, LinkedIn, GitHub, notice, start date, relocation, current organization), use `candidate-profile.md` and submit without asking. If it asks for a fact that is genuinely new, park.

## The apply loop

One job at a time, sequentially, on one tab.

1. **Open the job** from the row's Link. Use the site's safe URL pattern from its reference.
2. **Preflight the page:** duplicate state, external-apply smell, years, salary, role fit. Decide apply or skip with a reason.
3. **Apply** using the site-specific flow. Read the live page before clicking; never reuse stale refs or selectors from an old snapshot.
4. **Fill required fields** from the resume and standing answers.
5. **Answer every custom question.** Follow `references/answer-rules.md`. Never leave a required question blank.
6. **Submit** and wait for the site's async state.
7. **Verify** on the site's own confirmation surface: a confirmation page, success heading, an applied state, or an application-history row. A click is not an application.
8. **Flip the Notion row immediately** from `Drafted` to `Applied` with the IST timestamp. Do not batch the writes to the end. If the write fails, keep the ledger entry, tell the user, and continue only if they say so.
9. **Record in the ledger:**
   ```sh
   python3 <skill-dir>/scripts/ledger.py add \
     --site "<Site>" --company "<Company>" --role "<Role>" \
     --salary "<Salary>" --yoe "<YOE>" --status Applied \
     --url "<url>" --applied-at "<YYYY-MM-DD HH:MM IST>"
   ```
10. **Pace: 90 seconds minimum.** After a verified submission, wait at least 90 seconds before opening the next job on that site. Count from the verification time, not from the click. The site reference's shorter pacing is a floor for page reads only; it never overrides this rule. On 429 / Cloudflare, wait and reload once, then stop.
11. Stop when the requested number of **verified** applications is reached, or the drafted queue is exhausted. Failed submissions do not count.

If a site-specific flow contradicts its reference, trust the live page, note the deviation, and update the reference at the end of the run.

## Update the Notion row

Use `references/drafted-queue.md` and `references/notion-logging.md`.

- Change **only** the `Status` cell to `Applied` and the `Applied At (IST)` cell to `YYYY-MM-DD HH:MM IST`.
- Keep every other cell byte-for-byte identical.
- Use `notion-update-page` with `command: "update_content"`, `old_str` = the exact fetched row, `new_str` = the same row with those two cells changed.
- Fetch the page again and confirm the row now reads `Applied` with the timestamp. The API response is not proof.
- If the same company + role already has an `Applied` row, do not add a second row. Tell the user.
- If the row is in an escaped paragraph (Shine, Hirist), replace the exact escaped line fragment, then verify. Do not rebuild the whole page.

## When to stop early

Stop and report instead of pushing through when:

- The site logs you out, shows a CAPTCHA/2FA challenge, or asks for credentials. Hand off to the user.
- A persistent 429 / Cloudflare wall survives the reference's wait-and-reload remedy.
- Three consecutive submissions fail for the same non-obvious reason. One retry per job is fine; blind replay is not.
- The page structure changed enough that the reference's selectors no longer find the apply control. Trust the live page, stop, and update the reference rather than improvising a submit.
- Notion is unreachable and the user wants logging guaranteed. Finish the current job, keep the ledger, and ask whether to continue.

Never "make it work" by inventing a field value, skipping verification, or trying an external ATS the user did not authorize.

## Reporting

End every run with:

```
Run: <Site> — <YYYY-MM-DD> (IST) — requested <n>, applied <n>, skipped <n>, needs answers <n>

| # | Company | Role | Salary | YOE | Status | Notion |
...

Skipped (grouped by reason):
- 2+ years (n): ...
- External ATS (n): ...
- Dead / removed (n): ...
- Already applied (n): ...
- Out of lane / unpaid (n): ...

Answers I filled: ...
Needs your answer (not submitted): ...
Notion: Job Applications -> <Site> (<url>)
Verification: each row above was confirmed on the site's own confirmation surface.
Running total today: <n> applications.
```

Then ask whether to continue with another batch or change a standing answer.

## Self-update protocol

Leave the skill smarter after every run:

1. Append a dated field note to `references/<site>.md` under `## Field notes (append-only)` in this shape: `- YYYY-MM-DD — observation — what you did — why it matters`. Capture selector changes, new question types, required fields, rate limits, and external-ATS patterns.
2. Update the standing answers in `references/candidate-profile.md` only for a durable new fact. Never put one-off answers there.
3. New site: create `references/<site>.md` from `references/new-site-template.md`, add it to the table above, and note it in the changelog.
4. Append a dated entry to `references/CHANGELOG.md` for every behavioural change.
5. Never store credentials, cookies, tokens, or unnecessary personal data. Standing answers and resume facts are the only personal data allowed.
6. Never edit the resume or the PDF. If a run reveals a resume error, report it to the user.

## Quick checklist

- [ ] Site and batch size confirmed (custom text available)
- [ ] Resume + candidate profile + answer rules + site reference read
- [ ] IST date/time captured
- [ ] Browser status checked; correct session
- [ ] Login verified on the rendered page, or user handed off
- [ ] Notion root reachable
- [ ] `Drafted` rows parsed with their exact original text
- [ ] Every job reopened and re-screened
- [ ] No role with a stated 2+ years minimum submitted
- [ ] At least 90 seconds between applications on the same site
- [ ] Every required question answered under the locked style
- [ ] Every submission verified on the site
- [ ] Each row flipped to `Applied` with the IST timestamp and verified
- [ ] Ledger updated
- [ ] Skips have reasons; report is honest
- [ ] Site reference and changelog updated
