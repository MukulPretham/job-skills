---
name: job-find
description: Find jobs that fit Mukul's resume and queue them as Drafted rows in the correct site page under Notion -> Job Applications, using the user's own logged-in browser. Use whenever the user says /job-find, "find jobs", "job search", "find me roles", "harvest jobs", "add jobs to Notion", "search Wellfound/Indeed/Cutshort", or asks to look for fresher full-stack, backend, software engineer, or AI engineer roles. Always asks which site and how many roles, creates a new Notion site page when that site has none, screens every live listing against the bundled resume, and never submits an application.
argument-hint: "[site] [quantity]"
---

# Job Find

Find live roles that fit the resume and queue them in Notion as **`Drafted`**. Finding is not applying. This skill never clicks a submit button, never fills an employer form, and never changes a row past `Drafted`.

The output of a run is: a set of verified live job listings, added as rows to one site page under `Job Applications`, each one screened against the resume and marked `Drafted`.

**Learning rule.** This skill must get better with every run. If you discover a new search URL, filter, card selector, login signal, rate-limit response, site quirk, or a new site that works, write it into the corresponding `references/` file before the run ends. Add a dated line to `references/CHANGELOG.md` for every behavioural change. A finding that stays only in the chat is lost.

## Read these first

| File | When | What it gives you |
|---|---|---|
| `resume/resume.md` | Every run | The canonical resume. If missing, stop and ask for it (see below). |
| `resume/mukul_pretham_resume_v5.pdf` | Every run | The PDF attached to applications. Never regenerate or edit it. |
| `references/candidate-profile.md` | Every run | Target roles, hard eligibility rules, standing answers, strong-match keywords |
| `references/site-search-playbook.md` | Every run | Per-site entry points, search UI, card extraction, login signals |
| `references/notion-board.md` | Before reading or writing Notion | Exact page hierarchy, table format, site-page creation, append and verify calls |
| `references/new-site-recon.md` | Site not in the playbook | How to map an unknown site without applying |
| `references/CHANGELOG.md` | Every run | What changed recently; append your own change |

**Resume bundle rule.** The resume is stored inside this skill so a later session never has to ask for it again:

```
<skill-dir>/resume/resume.md
<skill-dir>/resume/mukul_pretham_resume_v5.pdf
```

`<skill-dir>` is the absolute path of the folder containing this `SKILL.md`. At the start of every run, check both files exist. If either is missing, stop before searching and say exactly:

> "The resume bundle is missing from the job-find skill. Please send me `resume.md` and the latest resume PDF, and I will save both inside the skill so you never have to send them again."

When the user supplies them, copy them into `<skill-dir>/resume/`, keeping the names above, and re-read them. Do not proceed on memory of an old resume.

## The two questions, every run

Before touching the browser, ask the user two things. Use the `question` tool and ask both in one call. The tool automatically offers a free-text "Type your own answer" option, which is the custom block the user wants; never remove it or force a fixed choice.

Do one read-only `notion-fetch` of the root first, so the site options reflect the pages that actually exist. That is not a browser action and does not need permission; it just keeps the site list honest.

**Question 1 — site**

> "Which job site should I search?"

Options, in this order: `Wellfound`, `Indeed`, `Hiring Cafe`, `Cutshort`, `Shine`, `Hirist`, `Apna`. Add any other site already present under `Job Applications` in Notion. The user may type any other site name.

**Question 2 — quantity**

> "How many roles should I find in this run?"

Options: `5`, `10`, `15`, `20`. The user may type any number. If they say "as many as possible", propose 10, state that it is the working cap, and proceed only after they agree.

If the invocation already supplied both (`/job-find indeed 10`), use them and skip the questions. If it supplied one, ask only the missing one.

**Site names.** Keep the user's wording in chat, but use one canonical title in Notion. Map aliases before resolving the page:

| Canonical | Accept as |
|---|---|
| Indeed | indeed, in.indeed.com, indded |
| Wellfound | wellfound, well found, well-found, wellfound.com |
| Hiring Cafe | hiringcafe, hiring cafe, hiring-cafe, hiringcafe.com |
| Cutshort | cutshort, cut short, cutshort.io |
| Shine | shine, shine.com |
| Hirist | hirist, hirist.tech |
| Apna | apna, apna.co |
| LinkedIn | linkedin, linkedin.com |
| Naukri | naukri, naukri.com |

If the canonical site page does not exist, create it (see `references/notion-board.md`, section "Create a missing site page"). Tell the user you created it. Never create a duplicate because of an emoji prefix, casing, or an alias.

## Preflight

Do these in order.

1. **IST clock.** Run `python3 <skill-dir>/scripts/ist_now.py`, or `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M %Z'`. The date goes in the `Drafted` rows.
2. **Resume bundle.** Confirm `resume/resume.md` and `resume/mukul_pretham_resume_v5.pdf` exist and read the markdown. Read `references/candidate-profile.md`.
3. **Notion reachable.** Call `notion-search` for `Job Applications` once. Confirm the root page answers. If Notion is down, tell the user before searching; there is no point finding roles you cannot queue.
4. **Browser health.** This skill drives the user's real browser through the browser MCP. On this machine it is exposed as `browse`:
   - `tools.browse.status()` for relay, extension, and connected browsers.
   - `tools.browse.session_new({ id: "<site>-find" })` for an isolated tab, or the default session.
   - `tools.browse.execute({ code: ... })` runs Playwright: `page`, `context`, `snapshot()`, `ref()`, `handoff()`.
   - If the harness exposes `browser-control` instead, use `tools["browser-control"].execute` with the same Playwright code.
   - **Never add or configure an MCP server yourself.** If neither browser MCP is present, stop and tell the user to add the `browser-control` MCP before this skill can run.
5. **Login check.** Open the site and verify the signed-in surface in `references/site-search-playbook.md`. If the page shows Login / Sign up / Create account, stop and say:

   > "You're signed out of <site>. Please log in manually in the browser, then tell me when you're done."

   Wait for confirmation and re-check the rendered page. Never type a password, create an account, or solve a CAPTCHA. If a CAPTCHA or bot wall appears, use `handoff()` and let the user clear it.
6. **Ledger context.** Run `python3 ../job-apply/scripts/ledger.py list --site "<Site>" --limit 20` if the sibling skill is present. It prevents re-finding a role that was already applied to or drafted.

## Search protocol

**Browser only. No web search.** The job must be seen on the live site, in the user's logged-in browser, before it is written to Notion. A web-search result, an aggregator snippet, or a remembered URL is not a listing.

For each site, follow `references/site-search-playbook.md`. The shared shape is:

1. Open the site's own search surface (home page recommendations first where the playbook says so).
2. Use the site's search box and filters through the UI. Do not navigate to a parameterised search URL that the playbook marks as bot-flagged.
3. Collect listing links. De-duplicate by job id and by normalised URL.
4. Open each candidate job page live and read the description. A card is a lead, not a verified listing. If the page is dead, removed, or redirects off-site, drop it.
5. Screen it (next section). Keep or skip with a one-line reason.
6. Continue until the requested number of eligible, live, not-already-known roles is reached, or the site's eligible pool is exhausted.

Pace the site. Wait 2 to 3 seconds between job pages on Indeed; use the site-specific pacing in the playbook. Never hammer a 429 or Cloudflare wall. Wait, reload, and if it persists stop and report.

## Screening

Use `references/candidate-profile.md` for the full rules. The short version:

**In lane**

- Full stack, backend, software engineer, SDE, MERN, React + Node, Next.js, Python, Java / Spring Boot, Go
- Junior AI / LLM engineer, applied AI, agentic systems
- Junior DevOps / platform / SRE
- Paid internship or trainee role with real engineering work

**Hard skip**

- Any stated minimum of 2+ years, including "2+ preferred". Do not rationalise it.
- Senior, staff, principal, lead, architect, engineering manager, SDE II/III.
- QA, SDET, manual testing, L1/L2 support, night-shift operations, data/business analyst.
- .NET-only, PHP-only, SAP/ABAP, Salesforce, or another stack the resume does not support.
- Unpaid internship, training-plus-placement fee, commission-only, bond with a fee.
- External ATS or "apply on company site" only when the site is an aggregator that has no native apply. Record the employer URL if that is the real destination; otherwise skip.
- Already present in the site table or the ledger, duplicate listing, title and description that do not match, dead listing, mass-produced Ameerpet-style ₹1.3–3.9L ads, vague "any graduate" engineering listings.

**Case by case**

- "Fresher", "0–2 years", "entry level", "graduate", or no years stated with knowledge-based wording: eligible.
- "1+ years": eligible only if the JD also invites freshers, interns, or strong projects. If it reads mid-level, skip.
- "0–3 years" or "0–4 years": eligible; the lower bound is 0.
- Paid internship: eligible when the stipend is stated or clearly non-zero. "Contribution-based" counts as paid but flag it.
- Salary below ₹4 LPA is not an automatic skip. Unpaid is always a skip.

Every skip gets a one-line reason, kept for the report. The user must be able to override.

## Dedupe before writing

A role is "known" when any of these is true:

- The same company + role already exists on that site page in any status (`Drafted`, `Applied`, `Rejected`, and so on).
- The same normalised job URL already exists on that site page or another site page.
- `../job-apply/scripts/ledger.py check` returns `"match": true`.
- The live page itself shows an applied state (`✓ Applied`, "Applied", "You have already applied").

Company alone is not enough: one company can have several real roles. When a role is known, skip it and say so in the report. Never write a second row for the same company + role on the same site.

## Write the drafted rows

Read `references/notion-board.md` before the first write. The fixed format is:

```
| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |
| --- | --- | --- | --- | --- | --- | --- |
| Acme Corp | Backend Developer | ₹6,00,000/yr | 1+ yr | Drafted | 2026-11-11 (drafted) | [Job](https://...) |
```

Rules:

- **Status is always `Drafted`.** Never `Applied`. This skill does not submit.
- **Applied At (IST)** is `YYYY-MM-DD (drafted)` using today's IST date. It is the queue date, not an application time.
- **Salary** exactly as posted (`₹6,00,000/yr`, `₹25,000/mo`, `Not listed`). Never convert or invent.
- **YOE Required** is `Fresher`, `0-1 yr`, `0-2 yr`, `0-3 yr`, `1+ yr`, or `Not stated`, matching the most specific number the JD gave. Use the live page's own style if the column already has values like `0 yr`.
- **Link** is the live job URL you actually opened, as `[Job](url)`. If the site is an aggregator whose real apply target is the employer ATS, put the employer URL there and note the aggregator URL in the report.
- Escape a literal `|` in a company or role. Keep every cell on one line.

Write **one row per verified live listing**, and write it as soon as the listing clears screening. Do not batch the whole run into one giant write at the end. If a Notion write fails, keep the row in your run list, tell the user, and do not claim it was saved. Retry once from a fresh fetch; if it still fails, stop.

## Reporting

End with:

```
Run: <Site> — <YYYY-MM-DD IST> — requested <n>, drafted <n>, skipped <n>

| # | Company | Role | Salary | YOE | Link |
...

Skipped (grouped by reason):
- 2+ years (n): ...
- External / company site (n): ...
- Duplicate / already known (n): ...
- Out of lane (n): ...
- Dead or removed listing (n): ...

Notion: Job Applications -> <Site> (<page url>)
Notes: <anything the user should know: thin pool, bot wall, salary flags>
```

Then ask whether to draft another batch on the same site or move to a different site. Do not start applying.

## When to stop early

Stop and report, rather than forcing volume, when:

- The site logs you out, shows a CAPTCHA or 2FA, or asks for credentials. Hand off to the user.
- A persistent 429 / Cloudflare wall survives the playbook's wait-and-reload remedy.
- Three consecutive job pages fail for the same non-obvious reason.
- The site's eligible pool is exhausted. Report the honest number; do not pad the list with ineligible roles.
- Notion is unreachable and the user wants the rows saved. Keep the run list and ask before continuing.

## Self-update protocol

Leave the skill smarter after every run. This is mandatory, not optional.

1. Append a dated field note to `references/site-search-playbook.md` under the site's section when a selector, search URL, filter, or login signal changed.
2. Add a new site section when you map a new site with `references/new-site-recon.md`.
3. Append a dated entry to `references/CHANGELOG.md` for every behavioural change. Say what changed and why.
4. Update `references/candidate-profile.md` only for durable new facts or standing answers. Never put one-off answers there.
5. Never store credentials, cookies, tokens, or unnecessary personal data in the skill. The resume and standing answers are the only personal data allowed.
6. If the live site contradicts the playbook, the live site wins for this run. Record the deviation.

## Quick checklist

- [ ] Site and quantity confirmed with the question tool (custom text available)
- [ ] Resume markdown and PDF present in `resume/`
- [ ] Candidate profile and site playbook read
- [ ] IST date captured
- [ ] Notion root reachable
- [ ] Browser MCP healthy; correct session
- [ ] Site login verified on the rendered page, or user handed off
- [ ] Site page exists, or created once as a direct child of `Job Applications`
- [ ] Existing rows and ledger checked for duplicates
- [ ] Every job page opened live and screened
- [ ] No role with a stated 2+ years minimum drafted
- [ ] Rows written with status `Drafted` and `YYYY-MM-DD (drafted)`
- [ ] Writes verified by re-fetching the site page
- [ ] New findings written into the site playbook and `references/CHANGELOG.md`
- [ ] Report lists drafted, skipped, reasons, and the Notion link
