# Hiring Cafe — Site Runbook

**Scope:** this run screens on `hiringcafe.com` only, but every application is finished on the **employer's own ATS**, because Hiring Cafe is an aggregator. The user explicitly authorized external ATS flows for this site on 2026-11-03 ("links will go into the company's site, figure out each one").

Site name in Notion: **Hiring Cafe**.

## 1. Golden rules

1. Hiring Cafe never hosts an application form. The "Apply directly on employer's site" button opens a Workable / Ashby / Rippling / Greenhouse / Lever / Eightfold / Oracle / SmartRecruiters / company page. You must drive that site yourself.
2. **Never click the apply button to discover the URL.** The employer URL is already in the job page HTML. Read it (see §3) and navigate directly. Clicking the button loses the tab in popups and, on Workable, opens a modal that then swallows the next click.
3. The Hiring Cafe job page is the **fresher gate**. It shows a structured YOE badge (`0+ YOE`, `1+ YOE`, `1.5+ YOE`, `2+ YOE`) plus the first sentence of the requirement. Read both; the badge alone is not enough.
4. **`IN YOUR TRACKER → Applied` on the job page means already applied.** Skip it even if the local ledger has no entry. But treat it as a **weak, session-local** signal: it is rendered from the browser's own state and does not survive a new session, another machine, or a cleared profile. The authoritative applied record for this site is Notion, so every batch starts with the §4.0 sweep.
5. One job at a time, one employer tab at a time. Verify on the employer's confirmation surface before counting it.
6. The browser tab group may be closed by the user mid-run. Re-read `context.pages()` before every step; never reuse a stale page handle from `state`.

## 2. Setup and session

- Session name: `hiringcafe` (`session_new({ id: "hiringcafe" })`).
- No login is required to browse, search, or reach employer apply links. Do not sign in, do not create an account.
- Home page defaults to US jobs and a US state list. Set the location chip to **India** before searching, otherwise results are US-only.
- The left rail is `Classic` view (`/classic`). That view is the only one that renders `data-quick-job-card` cards with YOE badges. Use it.

## 3. Quick reference: URLs and selectors

| Thing | Value |
|---|---|
| Search (classic) | `https://hiringcafe.com/classic?searchState=<urlencoded JSON>` |
| Job page | `https://hiringcafe.com/job/<slug>-<hash>` |
| Company page | `https://hiringcafe.org/org/<domain>` (not needed) |
| Job cards | `[data-quick-job-card="true"]` |
| Job link in card | `a[href^="/job/"]` |
| Search box | `getByRole("combobox", { name: "Job title or keyword" })` |

`searchState` is URL-encoded JSON. Useful keys:

```json
{
  "searchQuery": "backend developer",
  "seniorityLevel": ["No Prior Experience Required", "Entry Level"],
  "applicationFormEase": ["Simple"]
}
```

`applicationFormEase: ["Simple"]` is the single best filter for this site: it keeps only postings whose employer form does not require account creation or resume reformatting. It cut 58 fresher-eligible backend roles to 24 and every one of them was a short Workable/Ashby/Rippling form.

**Extract the employer apply URL from the job page** (do this instead of clicking):

```js
const urls = await page.evaluate(() => {
  const html = document.documentElement.innerHTML;
  return [...new Set((html.match(/https?:\/\/[^"'\\\s<>]{10,180}/g) || []))]
    .filter(u => !u.includes('hiringcafe') && !u.includes('posthog') &&
                 !u.includes('w3.org') && !u.includes('schema.org') &&
                 !u.includes('tally') && !u.includes('reddit') &&
                 !u.includes('googleusercontent') && !u.includes('googletagmanager') &&
                 !u.includes('doubleclick') && !u.includes('linkedin.com/company'));
});
```

The first result is usually the company homepage, the second/third is the ATS job URL. Recognise it by host: `jobs.ashbyhq.com`, `jobs.workable.com`, `ats.rippling.com`, `job-boards.greenhouse.io`, `jobs.lever.co`, `*.eightfold.ai`, `*.oraclecloud.com`, `jobs.smartrecruiters.com`.

**Extract the whole card list**:

```js
const cards = await page.evaluate(() => Array.from(document.querySelectorAll('[data-quick-job-card="true"]')).map((c, i) => ({
  i,
  t: (c.innerText || "").replace(/\n+/g, " | ").slice(0, 260),
  job: c.querySelector('a[href^="/job/"]')?.getAttribute("href") || null,
})));
```

## 4. Finding candidate jobs

### 4.0 Pre-batch applied set — mandatory, before the first job page

Hiring Cafe does not maintain an account-level applied state. `IN YOUR TRACKER → Applied` is rendered from the current browser session, so after a restart, a different machine, or a cleared profile every previously applied job looks fresh. Applying twice to the same role is then indistinguishable from a first application, and it is a bad look to the employer.

So the batch starts with a sweep of **the single `Hiring Cafe` page in Notion** (all dates share one table since the 2026-11-07 restructure), and that set is what "already applied" means for the rest of the run.

**Procedure (deterministic — walk the tree, do not trust search ranking):**

1. Resolve the root `Job Applications` page by `notion-search` and confirm the title is exactly `Job Applications` (known ID `40d3109c-a531-8132-847b-e945a98a70a1`).
2. Fetch the root and pick the child page titled `Hiring Cafe` (accept `HiringCafe`, `Hiring Cafe` case-insensitively, ignore the ☕ emoji). There is **no date layer** — if you ever find date pages, they are archived leftovers, not the live table.
3. Fetch the `Hiring Cafe` page and parse the application table rows. Read **every** row regardless of its `Applied At` date.
4. Build two keys per row and treat a hit on **either** as already applied:
   - **company + role**, normalized: lowercase, collapse whitespace, strip punctuation and legal suffixes (`inc`, `ltd`, `pvt`, `technologies`, trailing `.ai`).
   - **employer ATS URL**, normalized: strip the query string and trailing slash, lowercase the host. (`?gh_jid=...` and `?source=...` change per visit.)
5. Cross-check against the ledger (`ledger.py list --site HiringCafe --limit 200`). A ledger row missing from Notion means a Notion write failed — add it to the set anyway and repair Notion before applying.
6. Record the sweep result in the `Run Notes` entry (row count, distinct companies, date range covered) so the next agent can see it actually ran.

**Traps, all observed:**

- **`Run Notes` and `Hyderabad Outreach` match a `notion-search` for "Hiring Cafe"** because their body text names the site, and `Run Notes`' summary table parses like an application table. Filter on the result's **title being exactly `Hiring Cafe`**, or walk the tree instead of searching. A search-only sweep will pollute the set with "Wellfound / Requested / Verified" rows.
- **Rows at `Drafted` were never submitted.** They are not prior applications, but they are known roles: check the ledger and re-verify before opening them as new.
- **One company, several roles is legitimate.** Rubrik had two distinct reqs on 2026-11-04. Key on company **+ role**; dedupe by company alone and you silently drop real openings.
- **Titles drift between the card, the ATS, and the row.** Match on normalized company + a role token overlap rather than exact strings.
- **A Notion row written by another harness or another day still counts.** The sweep is date-blind on purpose.
- **Re-applying is not a "duplicate" you can fix later.** There is no site-side undo and no application history to audit, which is exactly why this sweep exists.

Minimum expected volume after a few runs: ~20+ rows (21 on 2026-11-07). If the sweep returns zero rows, stop and check the root page and title filter before concluding there are no prior applications.

### 4.1 Queries and filters

1. Location → India (keep Remote/Hybrid/Onsite all checked).
2. Search one of: `backend developer`, `full stack developer`, `software engineer`, `python developer`, `java developer`, `AI engineer`, `react node developer`.
3. Open **Filters → Experience** → check `No Prior Experience Required` + `Entry Level`.
4. Open **Filters → Apply Process** → check `Simple Application Forms`.
5. Read the card list from §3. Sort by recency mentally using the `1d / 23h / 1w / 1mo` prefix.
6. **Run several queries per batch.** One query yields roughly 15–25 usable cards, and the fresher-eligible subset is small (often 3–6). Across `backend developer`, `full stack developer`, `software engineer fresher`, `python developer`, `AI engineer`, and `react developer`, the same roles repeat, so dedupe by `/job/` slug. Keep the eligibility pool in a list before opening any job page.
7. The `No Prior Experience Required` + `Entry Level` filters still return many `1+ YOE` and `1–3 years` roles. Treat the filter as a loose pre-filter, not a guarantee.

The card text is `age | title | location | salary? | work mode | commitment | company: blurb | YOE badge + requirement sentence | tools`. That is enough to screen most jobs without opening them.

## 5. Screening

| Card signal | Verdict |
|---|---|
| `0+ YOE`, `0-1 year`, `0-3 years`, `0-2 years` | Eligible |
| No YOE badge at all + knowledge/shipping-based requirements | Eligible (`Not stated`) |
| `1+ YOE` with "freshers welcome" / internship / early-careers wording | Case by case, per the hard rule |
| `1.5+ YOE`, `2+ YOE`, `3+ YOE` | **Hard skip** |
| Senior / Staff / Lead / SDE II / Manager in the title | Skip |
| QA / SDET / Support / Data Engineer / `.NET`-only | Skip |
| Job page shows `IN YOUR TRACKER → Applied` | Skip — already applied |
| Internship with no stipend stated | Case by case; a full-time "Apprentice" contract at a funded startup counts as paid |
| JD says IIT/NIT/IIIT (or "Tier 1 college") only | Skip — GNIT is not in that set; this is a hard eligibility screen, not a preference |
| JD says "only apply if you are a <city> resident" and it is not Hyderabad | Skip — do not claim a false address |
| Employer page's location list omits India even though the Hiring Cafe card said "Asia" | Skip — read the employer page, not the card |

Salary formatting from this site: it renders ranges like `₹1500k-₹3000k/yr`, `₹25k-₹35k/mo`, `undefined600k-undefined800k/yr` (broken data — treat as `Not listed`).

## 6. The apply flow

### 6a. Ashby (`jobs.ashbyhq.com`) — best case, ~4 fields

1. Go straight to `<jobUrl>/application`.
2. `#_systemfield_resume` → `setInputFiles(<resume pdf>)`. Wait ~4s.
3. Name and email usually autofill from the resume. Only fill if empty:
   `#_systemfield_name` → `S Mukul Pretham`, `#_systemfield_email` → `mukulpretham@gmail.com`.
4. Fill any URL field with `https://linkedin.com/in/mukulpretham`.
5. Click `Submit Application`. Success surface: heading **Success** + "Your application was successfully submitted."
6. Invisible reCAPTCHA passed unattended both times. No handoff needed.

### 6b. Rippling ATS (`ats.rippling.com`) — ~8 fields, CV autofill does most of it

1. URL redirects to `/en-GB/<company>/jobs/<id>`. Click **Apply now**.
2. `input[type=file]` (first one, under `CV*`) → `setInputFiles(<resume pdf>)`. Wait ~6s.
3. The CV parser fills First name, Last name, Email, Current company, and the phone dial code + number. Verify, do not re-type over it.
4. **Location\*** is a combobox with `aria-haspopup="listbox"` and no placeholder. Click it, type `Hyderabad`, then click the option `Hyderabad, Telangana, India`.
5. EEO (gender / race / veteran) is voluntary — leave unselected.
6. SMS consent radios: choose **No – I do not consent to receiving text messages** (privacy-preserving default; the user has not opted in).
7. Submit with `button[type="submit"]`. Success surface: a `Confirmation` page with "You have successfully applied for <role>" and a "See all openings" button. **The page body text still contains the form afterwards** — take a screenshot or read the labelled button context, not `innerText`, to confirm.

### 6c. Workable (`jobs.workable.com`) — modal form, custom questions

1. The job URL slug may rewrite itself on load; re-read `page.url()`.
2. Click **Apply now** — it opens a **modal in the same tab**, not a new tab. If the click times out with "`[data-role="modal-wrapper"]` intercepts pointer events", the modal is already open: stop clicking and inspect it.
3. Modal fields: `#firstname`, `#lastname`, `#email`, `#input_phone` (country code already `+91`; enter `9059015626`), required resume file input (the **second** file input; the first is an optional photo), optional `#cover_letter`.
4. Custom questions are `textarea#QA_<id>` in DOM order and mirror the visible question text. Answer from standing answers:
   - earliest joining date → `Immediately / ASAP`
   - current CTC/Stipend → `0 (fresher, 2-month internship)`
   - expected CTC/Stipend → `₹4,00,000 per annum`
   - yes/no questions → answer honestly from the resume, never invent
5. Yes/No radios: the `<input>` is `aria-hidden` and `tabindex="-1"`, so `.click()` on the text does nothing and the input ids change on every render. Click the label instead:
   `locator('label:has(input[value="false"][name="QA_<id>"])').click({ position: { x: 5, y: 5 } })`
   Then re-read `input.checked` to confirm.
6. Submit with the `Submit application` button. The success surface is a "Thank you" panel inside the modal.

### 6d. Lever (`jobs.lever.co`) — ~7 fields, 1 visible hCaptcha

1. Open the job URL; the apply form is **not** on the page — click `APPLY FOR THIS JOB` (navigates to `<jobUrl>/apply`).
2. Fields: `input[name=name]`, `input[name=email]`, `input[name=phone]`, `input[name=org]` (Current company, **required** — use `Fresher - Student`), `input[name="urls[LinkedIn]"]`, `#resume-upload-input`.
3. **Location is a combobox with an autocomplete list.** Typing alone leaves the hidden `selectedLocation` empty and the field unsaved. Do: click `#location-input` → `type('Hyderabad', {delay:120})` → `ArrowDown` → `Enter`. Correct state is `location = "Hyderabad, Telangana, IND"` **and** `selectedLocation` containing JSON.
4. Custom questions arrive as `cards[<uuid>][fieldN]` inputs/textareas with visible labels. Hevo's were: Current CTC, Expected CTC, Notice Period, "5 days WFO at HSR Layout — comfortable?".
5. **Submit is blocked by a visible hCaptcha checkbox** (`#h-captcha`, iframe "Widget containing checkbox for hCaptcha security challenge"). The click times out with `...hCaptcha... iframe ... intercepts pointer events`. Do not retry the click. Call `handoff("...tick the hCaptcha checkbox...")`; the user ticks it and the page then submits and lands on `/thanks`.
6. Success surface: `/thanks` with heading **"Application submitted!"**.

### 6e. SmartRecruiters Easy Apply — 2-step wizard, shadow DOM

1. Click "I'm interested" with `page.getByText("I'm interested", { exact: true }).first().click({ force: true })`. A `getByRole('button', ...)` lookup does **not** match — the control is not a normal button.
2. It navigates to `jobs.smartrecruiters.com/oneclick-ui/company/<Company>/publication/<id>?dcr_ci=...`. No account is created. Step 1 = Personal information + Experience* + Education* + Profiles + Resume.
3. Fill names/email/confirm-email/phone. **City is a combobox**: click → `pressSequentially('Hyderabad')` → `ArrowDown` → `Enter`.
4. **Experience and Education are `Add` buttons that expand inline forms** (not modals). Combobox fields (Title, Company, Office location, Institution, School location) must be committed with `ArrowDown` + `Enter`, or the wizard shows `Error Title is required` and refuses to save. From/To are flatpickr month pickers: click and `keyboard.type('06/2026')`, then `Escape`. Typing twice concatenates (`05/202705/2027`) — use `.fill()` to correct.
5. **The resume file input is `#spl-dropzone-file-input-1`**, not the first `input[type=file]` (the first one is the profile photo and only accepts images; uploading a PDF there throws "file format is not supported").
6. Click `Next` → step 2 `.../screening`. Questions live in **nested shadow roots**; `document.body.innerText` shows none of them. Read them from the `sr-question-form-ai-banner[definition]` JSON inside `sr-screening-questions-form`.shadowRoot, which gives label / type / required / option labels in order.
7. Radio options are unlabelled in the aria snapshot (`radio "radio"`). Snapshot refs appear in question order, so map them by position and click in DOM order; each checked radio then reports `radio "question_<uuid>"`, which confirms the mapping.
8. Select comboboxes by clicking and choosing `getByRole('option', { name, exact: true })`. If the option is "outside of the viewport", use keyboard instead: click the combobox → `ArrowDown` ×N → `Enter`. Verify by reading `.inputValue()` on the combobox ref.
9. Success surface: `.../success` with heading **"Application submitted!"** and "You'll receive a confirmation email shortly."

### 6f. Dover (`app.dover.com/apply/...`)

- Redirects to `jobs.dover.com/<companyId>/<jobId>`; the SPA needs ~10s before the form renders (`document.body.innerText` is empty at 5s).
- Fields: `name=firstName|lastName|email|linkedinUrl|phoneNumber`, two `input[type=file]` (the **second** is the resume; the first is the autofill-from-resume dropzone), plus UUID-named custom fields whose labels are **not** in the DOM (`labels[0]` returns a zero-width space). Read the question text from the tail of `document.body.innerText` instead, which lists every question in order under `Apply`.
- Dover roles in this lane tend to ask 4–6 long behavioural essays (rejected AI-generated code, edge case spotted pre-build, hardest root-caused bug, feature across two layers). **Those are unanswerable without inventing incidents — park the job and ask the user** rather than writing a plausible story.
- Presents a Cloudflare Turnstile widget; expect a handoff if it does not auto-pass.

### 6g. Other ATS seen in the wild (untried, expect the same shape)

`job-boards.greenhouse.io` / `job-boards.eu.greenhouse.io` (Binance used the EU board; form = first/last/email/country/phone/resume/cover letter, but **the employer page's location list can be narrower than Hiring Cafe's** — check it before filling), `*.eightfold.ai`, `*.oraclecloud.com`, `careers.<company>.com`. Oracle and Eightfold want an account — treat as time-consuming and prefer the `Simple Application Forms` filter so they never appear.

## 7. Answers to fill without asking

All standing answers from `candidate-profile.md` apply. Site-specific additions:

| Field | Value |
|---|---|
| Resume upload | `../job-find/resume/mukul_pretham_resume_v5.pdf` |
| Name (single field) | `S Mukul Pretham` |
| First / Last name | `S Mukul` / `Pretham` |
| Phone (with +91 prefix shown) | `9059015626` |
| Location combobox | `Hyderabad, Telangana, India` |
| Current company | `Lupira` (autofilled from CV) |
| LinkedIn / Homepage URL | `https://linkedin.com/in/mukulpretham` |
| SMS / marketing consent | **No** |
| EEO gender / race / veteran | leave blank (voluntary); when the ATS forces a value, pick `Decline to self-identify` |
| Current employer | `Fresher - Student` (Lupira was an internship that ended Aug 2026, not current employment) |
| Employment status | Not currently employed. Last role: Full-Stack Intern at Lupira, Jun–Aug 2026. Final-year B.Tech student, graduating 2027 |
| Highest completed degree | B.Tech CSE (AI & ML) — final year, graduating 2027 (do not claim it is completed) |
| Work authorization (India) | Authorized without visa; do not require sponsorship |
| English proficiency (self-rating) | `Advanced` — honest for a working professional level; do not pick `Fluent`/`Native` |
| Team management | No |
| Offers in hand | No |
| Certifications | freeCodeCamp Back End Development and APIs (Feb 2025); Stanford/DeepLearning.AI Supervised Machine Learning (Jun 2025) |

## 8. Verification

Only these count as submitted:

| ATS | Success surface |
|---|---|
| Ashby | `Success` heading + "Your application was successfully submitted." |
| Rippling | `Confirmation` page + "You have successfully applied for <role>" |
| Workable | "Thank you" panel inside the modal |
| Lever | `/thanks` URL + "Application submitted!" |
| SmartRecruiters | `/success` URL + "Application submitted!" + "You'll receive a confirmation email shortly." |
| Dover | Confirmation panel after Turnstile passes (not yet observed) |

Then write the ledger entry and the Notion row **before opening the next job**. Also record the employer ATS URL, not the hiringcafe.com job URL, in the `Link` cell — that is where the application actually lives.

## 9. Rate limits, pacing, failure signatures

- No rate limiting, no Cloudflare, no CAPTCHA wall observed on hiringcafe.com itself.
- Ashby's invisible reCAPTCHA passed unattended.
- **Lever and Dover add their own captchas.** Lever shows a visible hCaptcha on `Submit application`; Dover shows Cloudflare Turnstile. Both need `handoff()` — do not hammer the submit button.
- SmartRecruiters does not show a captcha on the Easy Apply path, but its screening questions are invisible to `document.body.innerText` (nested shadow roots) and its comboboxes require ArrowDown+Enter to commit.
- `undefined600k-undefined800k/yr` in a card means the salary parser failed — record `Not listed`.
- **Card badges can overstate eligibility.** Kulfi showed `1+ YOE` but the JD said "0-1 years; strong fresh graduates welcome"; Merkle Science showed no badge but required IIT/NIT/IIIT. Always open the job page and read the requirement text.
- **Tab churn:** after a submit, employer tabs sometimes close themselves and `context.pages()` shrinks. A `Target page, context or browser has been closed` error means re-bind every handle from `context.pages()` before continuing. Never assume `state.job` / `state.ats` is still alive. Note that `targetUrl` selectors break as soon as the tab navigates to the employer domain — after the first hop, use `targetIndex: 0`.
- **User closing the tab group** wipes every page. Restart from `https://hiringcafe.com/classic?searchState=...`; the Notion rows and ledger entries already written are the recovery point.
- A submit whose tab died before the confirmation surface was read is **unverified**. Do not count it, do not blind-replay it (the application may have landed). Prefer a different job for that slot.

## 10. Reporting

Same shape as `SKILL.md`. Add: the employer ATS host per row (Ashby / Rippling / Workable) so the user knows where to look for replies.

## 11. Hard rules

- Never apply from hiringcafe.com itself — there is nothing to apply to there.
- Never skip the `IN YOUR TRACKER → Applied` check.
- Never start a batch before the §4.0 Notion-wide applied sweep. `IN YOUR TRACKER` alone is not evidence — it is session-local and forgets.
- Never invent a Workable custom-question answer; park the job instead.
- Never sign in, create an account, or upload anything other than the resume PDF.
- Never submit an EEO / demographic self-declaration.

## Field notes (append-only)

- 2026-11-03 — First run on this site (3 applications: Rippling, AiPrise, Build AI). — Mapped `/classic` search, the `searchState` JSON, `data-quick-job-card` extraction, and the HTML-embedded employer apply URL. — Clicking "Apply directly on employer's site" is a dead end (no navigation, no popup); reading the URL out of the HTML is faster and safer. Recorded as golden rule 2.
- 2026-11-03 — The job page renders `Saved / IN YOUR TRACKER / Applied` for a job the user had already applied to (Digitals AI), while a fresh job showed `Save job / Track / Hide`. — Used it as the duplicate signal and skipped. — This is the only duplicate protection the site offers without an account, and it caught a job that was absent from the local ledger.
- 2026-11-03 — Rippling's confirmation page keeps the whole application form in `document.body.innerText`. — Reading `innerText` looked like a failed submit; `screenshotWithLabels` showed the `Confirmation` heading and the "successfully applied" line. — Always confirm Rippling with a screenshot or a targeted selector, not body text.
- 2026-11-03 — Workable's "Apply now" opens a same-tab modal; a second click times out because the modal's header intercepts pointer events. — Stopped clicking and inspected the already-open modal. — Documented in §6c step 2.
- 2026-11-03 — Workable yes/no radios are `aria-hidden` inputs whose ids are regenerated on each React render. — Clicked the wrapping `<label>` at an offset and verified `input.checked`. — Documented in §6c step 5.
- 2026-11-03 — An Origin (Workable) application was submitted but the tab group was closed by the user before the success panel could be read. — Did not count it, did not replay it, and used Build AI for the third slot instead. — Uncertain sends stay unverified; the slot gets a different job.
- 2026-11-03 — Second run, 3 verified: Hevo Data (Lever), SAP (SmartRecruiters), Eurofins (SmartRecruiters). — Mapped the Lever, Dover, and SmartRecruiters Easy Apply flows; added §6d–6f. — The `Simple Application Forms` filter now routinely surfaces Lever, SmartRecruiters, and Dover, not just Workable/Ashby/Rippling, so those flows need first-class instructions.
- 2026-11-03 — Lever's location field silently keeps an empty `selectedLocation` when you only type and click the first suggestion text. — Typed, pressed ArrowDown then Enter, and confirmed `location = "Hyderabad, Telangana, IND"` plus a JSON `selectedLocation`. — A typed-only location may submit blank or fail server validation.
- 2026-11-03 — Lever submit was blocked by a visible hCaptcha iframe; the click timed out with "iframe ... intercepts pointer events". — Called `handoff()`; the user ticked the box and the page submitted to `/thanks` on its own. — One handoff is faster and safer than retrying or trying to solve it programmatically.
- 2026-11-03 — SmartRecruiters "I'm interested" is not matched by `getByRole('button')`, and its screening questions do not appear in `document.body.innerText`. — Used `getByText(..., {force:true})` and parsed `sr-question-form-ai-banner[definition]` from the shadow root. — Without the definition JSON you cannot see question text or option labels at all.
- 2026-11-03 — SmartRecruiters combobox options are often "outside of the viewport", so `option.click()` fails. — Committed them with click → ArrowDown → Enter and verified via `.inputValue()`. — Documented in §6e step 8.
- 2026-11-03 — Kulfi (Dover) had a perfect 0–1 year fit but 6 behavioural essay questions about personal engineering incidents. — Parked the job instead of writing plausible-sounding stories. — Inventing an incident would put a false claim in front of a hiring manager; the skill's "never invent" rule applies to essays too.
- 2026-11-03 — Several cards overstated or understated eligibility: Kulfi showed `1+ YOE` for a 0–1 role; Merkle Science showed no badge but required IIT/NIT/IIIT; Binance listed "Asia" but the employer board excluded India; Explorance required Chennai residency. — Opened every job page and read the requirement text before applying. — Four of the first six candidates were eliminated this way; the card alone is not a screening decision.
- 2026-11-04 — `session_use({id:"hiringcafe"})` does NOT stick when a second agent shares the same `browser-control` MCP process: the next `execute` ran in the other agent's `wellfound` session. — Passed `session: "hiringcafe"` explicitly on every single `execute` call for the rest of the run. — Without the explicit session id you will silently drive another site's tab, which is both wrong and unsafe in concurrent runs.
- 2026-11-04 — `execute` rejects multi-line code blocks that declare `const` at top level, but one-line `;`-separated scripts work. — Built every script as a single string with statements joined by `;`, and composed it in the outer Code Mode sandbox. — Saves a failing round trip on every navigation.
- 2026-11-04 — Greenhouse **iframe embed** (`job-boards.greenhouse.io/embed/job_app?for=...`) renders no options for the `Location (City)*` react-select: `aria-expanded` flips true but `#react-select-...-listbox` never mounts, so the field can never be committed. — Tried focus+type, dispatch mousedown, and option clicks; all left the value empty. Parked Nasuni (`nasuni.com/...gh_jid=5455190008`) and Ensono (`ensono.com/...gh_jid=4749950005`). — Any employer-site Greenhouse embed with a required location is a dead end under automation.
- 2026-11-04 — The same react-select bug also hits **direct** `job-boards.greenhouse.io` boards that ask for Country* + Location (City)*: selecting "Hyderabad, Telangana, India" sets the value for a moment and then clears it, and the Country listbox only ever offers phone-dial-code options. — Parked SingleStore intern (8154399), HackerRank intern (8229735) and NK Securities (4953876101). — Greenhouse boards that ask only first/last/email/phone/resume (SingleStore 8212128, Karya 5469564008) still submit perfectly, so check the field list before deciding.
- 2026-11-04 — BambooHR (`*.bamboohr.com/careers/<id>`) makes Address*, City*, Province*, Postal Code*, Country* mandatory. — Parked INVIDI (898) and HYCU (321) because the street address and PIN code are not in the resume. — Do not guess a PIN code; add "full postal address + PIN" to the standing answers before the next run.
- 2026-11-04 — Freshteam (`*.freshteam.com`) shows a visible "Are you a Robot?" reCAPTCHA (`size=normal`) that blocks the submit. — Clicked Submit once, saw the error, parked Quantela. — No handoff is possible in background runs, so treat Freshteam as captcha-gated.
- 2026-11-04 — Rubrik's own embedded Greenhouse form (`rubrik.com/company/careers/departments/job.<id>?gh_jid=...`) worked twice. It has an NDA full-name box, privacy = Yes, current employer = N/A, and a free-text `#location` (Google-Places dropdown, but free text is accepted). — The submit button sits below a Ketch cookie banner and Playwright reports "element is outside of the viewport"; hiding `#lanyard_root` and calling `el.scrollIntoView()` + `el.click()` submitted fine. Success = `/thank-you` + "Thank You For Applying".
- 2026-11-04 — Workable "What is your current compensation (INR)?" mangles text input (typing "0 (fresher...)" left "2"), and "How soon can you join?" is a **date** field (`DD/MM/YYYY`), not free text. — Used Ctrl+A + Backspace + typing single values, and 04/11/2026. — Wrong values silently reach the employer otherwise.
- 2026-11-04 — Three different overlays intercepted clicks across employer pages: Nasuni's OneTrust banner and sticky header, Rubrik's Ketch (`#lanyard_root`) and Google Places (`.pac-container`), and Workable's cookie bar. — Hiding those containers by `style.display='none'` before clicking the submit button was reliable. — Never force-click through them; the hidden container keeps intercepting.
- 2026-11-04 — Two Ashby tenants with extra questions (Certa: referral yes/no + sponsorship yes/no as `button[data-option]`; Consensys: "Why would you be a good fit?" + AI-recording consent radio group). — Answered with resume facts and picked the positive consent option; both reached the `Success` surface. — Ashby stays the cheapest ATS on this site.
- 2026-11-04 — Screened-and-skipped pool for this date (do not re-screen): Sun King, SuperApp, BotBuilt, PinSec, Prodigal, Botsync, Infor, Apna, ClickHouse, Branch, iCapital, RChilli, Smiths, Sauce Labs (Greenhouse combo), Cin7, Decisions, IMRIEL, Rippling SWE-1/FullStack (applied), AiPrise (applied), Build AI (applied), Hevo (applied), Hevo Associate SDE (same Lever URL as the applied intern role), Eurofins, Digitals AI, Merkle Science, Enterpret, Point72 IIT, Binance, Explorance (Chennai-only), HighRadius (top-tier IIT), ION (required hometown), Stripe (required graduation quarter), Acron (required graduation month), ArangoDB (JazzHR description mismatched the title).
- 2026-11-04 — `IN YOUR TRACKER → Applied` did **not** persist between the morning and evening sessions, and two agents running in parallel had no shared view of it at all. — Added §4.0: a mandatory Notion-wide sweep across every date before the first job page, keyed on company+role and on the normalized ATS URL, cross-checked against the ledger. — The site offers no application history and no undo, so a silent double-apply cannot be detected or repaired afterwards; the sweep is the only protection.
- 2026-11-04 — A `notion-search` for "Hiring Cafe" also returned the `Run Notes` page, whose summary table has the same pipe-delimited shape as an application table. — Filtered on the result title being exactly `Hiring Cafe` and confirmed each page's ancestry (`Job Applications / <date>`); a naive parse would have ingested `Wellfound / 10 / 10 / 51 / 0` as an applied job. — §4.0 documents walking the tree as the deterministic path and title-filtering as the fast one.
- 2026-11-04 — The sweep's first run found **16 applications across 2 dates** (6 on 2026-11-03, 10 on 2026-11-04), 15 distinct companies because Rubrik had two separate reqs. — Recorded the counts so the next run can tell a successful sweep from an empty one. — Company-only dedupe would have dropped the second Rubrik role, which was a legitimate Winter Intern posting.
- 2026-11-05 — **The pool is exhausted for this candidate.** Two agents, 30+ query buckets (`associate software engineer`, `java/python/node/react/devops/full-stack/SDE/AI-ML/product engineer`, `LLM/generative/agentic/RAG/FastAPI/MERN/Next.js/TypeScript`, intern/graduate/trainee, plus Hyderabad-localised variants), with and without the Simple-Application-Forms and seniority filters, produced 5 verified applications and no remaining eligible cards. — Every new hit was 2+ years, an account-creation ATS, a documented dead end, or captcha-gated. — Do not promise a 10-batch on this site again without a new posting influx; treat 5 as a realistic ceiling.
- 2026-11-05 — **Zoho Recruit (`*.zohorecruit.in` / `*.zohorecruit.com`) is captcha-gated**: the apply form carries a mandatory image challenge (`Type below image text`). Five genuinely eligible fresher roles died there — Vivusoft (AI Agent Engineer intern, 2026/2027 grads), Kavi Global (React intern), thinkbridge (AI-Native Product Engineer 0-1 yr), Altumind (GenAI fresher), Training Basket (LLM Engineer 0-1 yr). — Parked, listed for the user. — A background agent has nobody to hand to, so treat Zoho Recruit like Freshteam: park, never attempt to solve.
- 2026-11-05 — **Trakstar (`*.hire.trakstar.com`) can swallow a submit silently.** IMI Plc's form filled completely, Submit accepted, the form disappeared, and no confirmation or error text rendered; a fresh reload showed the form again with no already-applied state. — Recorded as unverified, not counted, not replayed. — An absent confirmation plus an absent error is not a success; the ledger must not gain a row.
- 2026-11-05 — `Voiceoc` (own careers page) requires a **hosted public resume URL**, and the candidate has none. — Parked rather than inventing a Drive link. — Add "public resume URL" to the standing answers or keep skipping this class of form.
- 2026-11-05 — **AkzoNobel / SuccessFactors** confirmed as a working path: submit lands on `/applythankyou?status=success` with "Thank you for your application. We have successfully received your application." (jobApplicationId returned). — Note its `Highest degree` dropdown has no in-progress option, so a final-year student has to pick the closest completed degree or park. — Second confirmed SuccessFactors surface after SAP.
- 2026-11-05 — `Lyric` (Ashby) surfaced only after ~30 query buckets; it was `Platform Engineer - Full Stack (UI Centric)`, no YOE stated, and applied cleanly. — Confirms Ashby remains the cheapest and most reliable ATS on this site. — When the pool looks empty, exhaust Ashby-hosted cards across synonym queries before concluding.
