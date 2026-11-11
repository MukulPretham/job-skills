# Wellfound (wellfound.com) — Site Runbook

**Scope:** this run applies on `wellfound.com` only. Do not open Indeed or any other job board while this reference is active.

This protocol comes from a real session with 21 verified applications. Re-read it at the start of every Wellfound run. If the live page contradicts it, trust the live page and append a field note at the bottom.

## 1. Golden rules

1. **Never apply twice to the same job.** Check the job page's own Apply state and `/jobs/applications` before every application.
2. **Never leave the custom question blank.** Every application must have a written answer.
3. **Answer style is locked:** simple, straight sentences, first person, no `--`, no em dash, no emoji, no bullet lists inside the answer, no markdown. It must read like a human typed it in 60 seconds. 2–4 sentences is the sweet spot (~250–360 characters). See `candidate-profile.md` for the recipe.
4. **Tailor every answer to that specific job description.** Read the JD first (inside the same execute, before filling), pick 1–2 facts from the JD and tie them to 1–2 resume facts. Never reuse a generic answer.
5. **Verify success, never assume it.** A successful apply shows the dialog heading `Success! Your application has been sent.` and the job page then shows a disabled `✓ Applied` button. The click alone is not proof.
6. **One application per execute chain, sequentially.** Do not parallelize apply flows on the same tab.
7. **Fresher gate:** any job whose JD or dialog says a minimum of 2+ years is a skip. No exceptions. `1+ years` is eligible when the JD invites interns, freshers, or strong projects.

## 2. Setup and session

- Use the `wellfound` browser-control session: `tools["browser-control"].session_use({ id: "wellfound" })` once per process. If it does not exist, use the default session and adopt the user's Wellfound tab if one is attached.
- Jobs page: `https://wellfound.com/jobs`
- Applications log: `https://wellfound.com/jobs/applications` (columns: Company | Role | Status | when)
- Logged-in check: the snapshot shows `button "Avatar for Sanku Mukul Pretham"`. If the page shows Login/Sign up, **stop and ask the user to log in manually**. Never attempt credential entry.
- **Relay restarts / session resets:** if `execute` returns URL `about:blank` or "No snapshot lines matched", the session page was recycled. Just `page.goto` the target URL again; nothing else is lost.
- If `page.title()` times out with `session-page/context-read-timeout`, wait and re-read after the page settles. Do not navigate away halfway.
- Keep `page.url()` in every diagnostic return.

## 3. Quick reference: URLs and selectors

| Thing | Value |
|---|---|
| Jobs list | `https://wellfound.com/jobs` |
| Saved-search chips | Should already be active: Software Engineer/DevOps/Backend/Architect/Engineering + Hyderabad + Full Time |
| Filters dialog | Button `Filters` on the list page |
| Job types | Checkboxes `Full Time`, `Internship`, `Contract`, `Cofounder` |
| Apply filter | `View results` at the bottom of the filter dialog |
| Hide external jobs | `checkbox "Hide jobs which require me to apply on the company's website"` at the top of results |
| Job page Apply | `button "Apply"` (main), plus `Apply now` lower on the page in some layouts |
| Application dialog | `role=dialog` headed `<h6>Apply to <Company></h6>`, then `Your Application` |
| Custom question box | Textarea with `id/name` like `customQuestionAnswers[377357][answer]` (the number changes per job) |
| Submit | `button "Send application"` |
| Success | `<h6>` heading `Success! Your application has been sent.` |
| Applied state | Main page button becomes `✓ Applied` (disabled) |
| Post-submit upsell | `Share your AI interview` heading + `checkbox "Share my AI interview"` (pre-checked) + `Save` button |

Stable way to find things: `snapshot({ find: /.../i, context: 1 })` — cheaper than a full snapshot. Full snapshots are capped; use `find` for actions.

## 4. Finding candidate jobs

### 4.1 Filters

- Job Types: `Full Time` + `Internship` (both checked) → around 355 results on the reference run.
- Then tick "Hide jobs which require me to apply on the company's website" to remove external listings (355 → 351). Do this every time; external ones still leak through as promoted rows.
- Standing criteria: **freshers/junior only, paid only (internships must be paid), student graduating 2027, Hyderabad-ish but remote OK.**

### 4.2 Role-name scan (cheap pass on the list page)

Scroll the list (`page.mouse.wheel`) then collect all links:

```js
const jobs = await page.evaluate(() => Array.from(document.querySelectorAll('a[href^="/jobs/"]'))
  .map(a => ({ href: a.getAttribute('href'), text: (a.innerText || '').trim() }))
  .filter(x => x.href && x.text));
return jobs;
```

Filter on the anchor text:

- **Keep:** `intern` (any), `junior`, `fresher`, plain `Software Engineer` / `Full Stack` / `Backend` / `Frontend` / `SDE`, `DevOps`, `AI Engineer`, `Data and AI Fresher`, product/engineering pairings that mention 1+ year.
- **Drop:** `Senior`, `Staff`, `Lead`, `Tech Lead`, `Architect`, `Principal`, `Engineering Manager`, `5+ yrs`, `QA`, `SDET`, `Testing`, `Support Engineer`, `Firmware`, `(Unpaid)`, `Founder's Office - Equity`, and any listing whose pay band reads senior (₹15L+ for a "no-prefix" full-stack role is usually mid+, but peek if unsure).
- **Drop:** `...-freelance` listings (Shopify freelance etc.) that demand a portfolio of live stores. Niche mismatch.

### 4.3 Per-job preflight (before clicking Apply)

Navigate to the job page (`/jobs/<id>-<slug>`), then in one evaluate grab:

```js
const st = await page.evaluate(() => {
  const applied = Array.from(document.querySelectorAll('button'))
    .some(b => (b.innerText || '').includes('Applied'));
  const h1 = document.querySelector('h1')?.innerText || '';
  const t = document.body.innerText.replace(/\s*\n\s*/g, ' | ');
  const exp = (t.match(/Experience[^|]*\|[^|]*\|[^|]*/) || [''])[0]; // dialog meta "Experience | 3+ years"
  const req = (t.match(/(\d\+? years[^|]{0,70})/) || [''])[0];         // JD text "... years ..."
  const applyAt = /apply at|apply by email|apply via/i.test(t);        // external-apply smell
  return { applied, h1, exp, req, applyAt };
});
return st;
```

Rules from preflight:
- `applied=true` → **skip immediately** (duplicate protection).
- `applyAt=true` → external application (for example "Make sure to apply at: http://..."). Wellfound's native Apply button may still look enabled; the click redirects off-site. Skip. Never chase it in a new tab.
- `exp` like `3+ | 4+ | 5+ years` → skip. `2+ years` → skip. `1+ years` is OK when the JD invites interns/freshers or says projects count.
- No salary shown at all for an internship → likely unpaid → skip. "Stipend: contribution-based" counts as paid but flag it in the report.
- JD asking for a portfolio of live Shopify/production stores or a specific niche the resume lacks → skip.

Then read enough of the JD body to write a tailored answer:

```js
const t = await page.evaluate(() => document.body.innerText.replace(/\s*\n\s*/g, ' | '));
const i = t.indexOf('About'); // or indexOf(h1.slice(0, 20))
return t.slice(i, i + 1500);
```

Look for their must-have skills list and one distinctive line (for example "agents that do real work, not demo chatbots") to echo in the answer.

## 5. The apply flow (peel-and-run template)

```js
// 1. Open the job page and check duplicate state.
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(2500);
// Optionally verify h1 and the absence of an "Applied" button.

// 2. Click Apply. The button literally says "Apply"; some pages also have "Apply now".
await page.getByRole('button', { name: 'Apply', exact: true }).first().click({ timeout: 15000 });
await page.waitForTimeout(3500); // the dialog renders late — wait first

// 3. READ the question text from the full dialog (see 5.1) — never guess it.

// 4. Fill the textarea with a freshly composed answer.
await fillInput(page.getByRole('textbox').first(), answer);
await page.waitForTimeout(800); // React needs a beat

// 5. Verify the value landed (the field sometimes resets silently).
const typed = await page.evaluate(() => (document.querySelector('textarea')?.value || '').length);
if (typed < 50) throw new Error('answer did not stick');

// 6. Find and click Send application.
const found = await snapshot({ find: /Send application/i, context: 0 });
// → returns like `- button "Send application" [ref=eNNN]`
await ref('eNNN').click({ timeout: 15000 });

// 7. Wait for the success heading (send is async, ~3–6s).
await page.waitForTimeout(6500);
const snap = await snapshot({ maxItems: 25 });
// expect: heading "Success! Your application has been sent."

// 8. Dismiss the AI-interview upsell.
// Leave the checkbox at its default (checked) and click Save.
await ref('eSuccessSaveRef').click({ timeout: 10000 });
```

### 5.1 Read the dialog — the important step

The compact `snapshot()` deliberately hides label text. It shows only `- textbox "customQuestionAnswers[377357][answer]"`, which is not the question. To know what the question says, read the dialog's full text:

```js
// Option A: detailed aria YAML (best)
const yaml = await ariaSnapshot();

// Option B: raw innerText
const dlg = await page.evaluate(() =>
  [...document.querySelectorAll('[role="dialog"]')].map(d => d.innerText.slice(0, 700)));
return dlg;
```

The dialog renders the question as plain text right before the textarea: for example `What interests you about working for this company?`.

Observed variants:
- `What interests you about working for this company?` (most common).
- The generic "why are you interested" ask.
- Some jobs have more than one custom question. If `customQuestionAnswers[...]` count > 1, expect multiple textareas and answer each. The user's rule: never leave one blank.
- Some dialogs contain Wellfound's own warning: `Improve your odds — It seems you're outside the years of experience preferred for this role (2+ years in Engineering role)...`. If the role requires 2+ years, **skip**. Do not continue just because the JD is vague.
- The dialog sometimes renders empty for 2–3 seconds after the click (`snapshot` shows `- dialog "Dialog"` only). That is a loading state. Wait 2.5–3.5 seconds and re-snapshot. Do not conclude the dialog failed.

### 5.2 Critical submit edge cases

1. **The Send button becomes disabled right after the click.** The same dialog reappears with the button `disabled` and the textarea visually gone (`textarea` query returns null, dialog text empty). This is the SENDING state, not an error. **Do not re-click.** Wait 4–7 more seconds; the heading `Success! Your application has been sent.` replaces `Your Application`. Observed on SonicAI and DeeplogicAI; the flow always completes.
   - A Google Analytics event `source_action=send job application` with `job_listing_id=...` fires at click time. It is a hint, not proof.
2. **If after a 10–15 second wait there is still no success heading and an error/validation text appears**, treat it as failed. Re-read the dialog, fix only what the page reports (for example a missing answer), and resend **once**. If a second attempt fails, report it and move on. Never blind-replay a submit more than twice.
3. **Textarea values can silently fail to stick.** Always verify length after `fillInput` (the `typed` check above). If it is 0, re-fill with `fillInput` on `page.getByRole('textbox').first()`. If it still fails, use the snapshot ref of the textbox. The string-selector fallback `querySelector('textarea')` exists.
4. **Refs go stale across navigations** (numbering restarts). Snapshot freshly right before every `ref()` click. Never reuse refs from an old snapshot after `goto`.
5. **Two Apply-text buttons exist on job pages** (`Apply` in the header and `Apply now` inline). Use the header one, `{ exact: true, .first() }`. Some layouts only have `Apply now` (DeeplogicAI, quavyn); the exact-name Apply then cannot be found, so fall back to snapshot find. On external-apply jobs, `Apply` is `disabled`, which is another external tell.
6. **Dialogs with no question** (only profile/verify text + Send) exist. In that case fill nothing. But the user's standing rule: if a textarea exists, it gets an answer. The observed fallback is that one textbox is the interests question.
7. **The success dialog contains a second decision:** `Share your AI interview` with a pre-checked checkbox. Default: leave the checkbox untouched and click `Save` to dismiss. Do not uncheck unless the user changes the preference.
8. **Success then page state:** after dismissing, the job page shows `✓ Applied` disabled both at the top and at the bottom-of-JD positions. That is the canonical "done" proof if you navigate away and come back.
9. **Dialog vs. new tab:** on native jobs everything stays in `page`. If clicking Apply changes the URL or opens an external site, that job was external. Navigate back in the same session page and skip it.

### 5.3 Confirm by state, not memory

At the end of each batch: `goto /jobs/applications`, wait 4 seconds, read the body text. Each row shows `Company | Role | Pending | N MINUTES AGO`. The role label in this list sometimes differs from the h1 (for example h1 `Full Stack Developer Intern at Timbre` shows as `Timbre | Full Stack Developer Intern`). Match by company, not exact string equality.

## 6. External and duplicate edge-case cheatsheet

| Signal | Meaning | Action |
|---|---|---|
| JD contains "apply at:" / "apply by email" / a careers@ link | External site job | Skip |
| `Apply` button disabled on load | Usually external or already applied | Read the page: if disabled with a JD email link → skip |
| `✓ Applied` present on load | Already applied | Skip (log it) |
| Promoted rows at the top of the list persist even with hide-external checked | External/ad | Skip |
| Same company already applied to today with a different role | Allowed, but avoid more than 2 roles per company/day (spam risk) | Prefer other companies first |
| Anchor text shows a pay band with `• No equity` only and no ₹/$ | Usually still paid; look for the word "Unpaid" explicitly | If literally `Unpaid` in the anchor → skip |
| Experience bar in the dialog (`Experience | 2+ years`) | Meta-level check | `1+` = OK; `2+` and up = skip (fresher rule) |

## 7. Answer-writing recipe

Use the resume hooks in `candidate-profile.md`. Formula:

1. One line naming what the company does and why it clicks with the user (from their JD phrase).
2. One line of proof from the resume (project/internship), using plain words.
3. Optional closing line tied to the role type (PPO path, remote, full-time-to-be).

Hard rules: no `--`, no `–`, no emoji, no markdown, no "I am a fresher", no `:)` style quirks. Keep it 2–4 sentences, plain ASCII with normal punctuation.

Sample (Marmeto):
> "I like that Marmeto builds integrations that businesses rely on every day. I have worked with Node.js, API integrations, and Redis based queues in my own projects, and this role lets me use exactly those skills while learning real world payment and logistics systems at a growing company."

Imagine the recruiter reviewing 200 applications this week: keep it that bare.

## 8. Reporting

Follow the report shape in `SKILL.md`. For Wellfound specifically, include:
- The `# | Company | Role | Pay | Resume hook in answer` table.
- The skipped list with the reason per skip (years bar, external, unpaid, QA, duplicate).
- A verification line: "all N confirmed on `/jobs/applications`, Pending, timestamps".
- A running total.
- A question asking whether to continue with another batch.

Name the skips the user cares about:
- confirmed duplicates from an earlier batch (`applied=true`)
- the exact JD phrase that excluded it (for example "3+ years in customer-facing delivery")
- companies already applied to twice today

## 9. Failure playbook

| Symptom | Handle |
|---|---|
| `about:blank` page / empty snapshot | Session page recycled → `goto` the target URL again |
| `page.title()` timeout | Wait, retry the read on the same page |
| Dialog blank after Apply click | Wait 2.5–3.5 seconds, re-snapshot (`ariaSnapshot()` for full YAML) |
| Send button stuck disabled >15 seconds, no success text | Read the dialog → one careful resend; else move on |
| Success not shown but no error either | Check `/jobs/applications` before assuming anything; timestamps show whether it landed |
| Analytics `net::ERR_CONNECTION_CLOSED` console noise | Ignore (blocked Google Analytics, unrelated) |
| Filter dialog missing after re-landing on /jobs | Re-open via `button "Filters"`, tick `Full Time` + `Internship`, then `View results` |
| "0 results" glitch right after landing | Transient render lag; re-read after 2–3 seconds or revisit |
| Login page appears | Stop entirely; a human must log in. Never type credentials. |
| Fill never lands (loopback on fills) | Use the snapshot ref of the textbox instead of the role selector |
| Page crashes with `chrome-error://` | A relay-owned tab will recreate on `goto`; user tabs are never force-replaced |

## 10. One-shot flow example

```
1. goto /jobs/4901481-backend-developer-integrations-automation
2. snapshot find /Apply/ → ref(eNNN) click
3. ariaSnapshot() → read: question = "What interests you about working for this company?"
4. compose from JD: Node.js + webhooks + Redis/BullMQ queueing ↔ CodeDrop Redis queues
5. fillInput → typed length 288
6. snapshot find /Send application/ → click ref
7. wait 4s → dialog STILL shows the form, button disabled (SENDING STATE — WAIT)
8. wait +5s → "Success! Your application has been sent." + AI interview share prompt
9. Save on the share prompt
10. page now shows button "✓ Applied" disabled (twice: header and Why-Join section)
```

If anything here contradicts the live page, trust the live page, note the deviation, and keep duration/identity from real evidence. Never claim an apply succeeded without both the success heading and the applications-page row.

## 11. Hard rules

1. Never apply twice to the same job.
2. Never leave a custom question blank.
3. Never submit a job whose stated minimum is 2+ years.
4. Never chase an external application off-site without explicit permission.
5. Never type credentials or create an account.
6. Always verify the success heading **and** the applications-page row.
7. Always report skips honestly, with the exact reason.

## Field notes (append-only)

Add new observations with a date. Do not delete earlier notes; correct them with a newer note.

- 2026-11-03 — Baseline protocol imported from `~/Desktop/well_found_apply.md`. No live run performed after import.
- 2026-11-03 — First live run (10 verified applications). The **Apply dialog's `Experience` bar is the authoritative fresher gate**, not the JD body: `transcurators Full Stack Developer` showed no years in the extracted body but the dialog said 3+ years, and `WeKnow Group Full Stack Developer` said "1–2 years" in the body while the dialog said 2+ years. Both were skipped after opening Apply. Screen by opening the dialog and reading `Experience`, then Cancel; never decide on body text alone.
- 2026-11-03 — `Junior`/`Associate` in the title does not imply eligibility: `VoiceQube Junior Software Engineer` = 2+ years, `Leadzen.ai Software Development Engineer` = 2–5 years. Check every one.
- 2026-11-03 — Internship listings frequently have **no** `Experience` bar in the dialog (Magi, Skoot, DialNext, Atom11, Eshal). Those passed the gate on title/pay/JD wording alone; treat an absent bar as "not stated", not as 0.
- 2026-11-03 — Dialog question variants seen: `What interests you about working for this company?` (most), the same with a trailing `*`, and `Cover Letter*` (Bhumio) where the interests question is absent and the only field is a required cover letter.
- 2026-11-03 — Some JDs put extra asks in the body that must be answered inside the note field: Skoot required a proudest-project link, last-internship detail, and a Claude Code/Codex repo. Answer length there went to ~450 chars on purpose; still no markdown, no dashes, plain sentences.
- 2026-11-03 — The list page's `Hide jobs which require me to apply on the company's website` checkbox has DOM id/name `showOffPlatformJobs` and was **already checked** on load, so the run started with external jobs hidden (329 results for the saved search).
- 2026-11-03 — Notion auto-links a bare domain in a table cell (`red6.ai` became `[red6.ai](http://red6.ai)`), so re-fetch the table text before every `update_content` append instead of reusing a remembered string.
- 2026-11-03 — Non-obvious screen-outs worth remembering: `Octasence` (Tier-1 institutes only, current students ineligible), `TaskLabs` (Google Form external apply), `Better` (email + Loom video), `éditor` and `zero4genz` (explicitly unpaid), `aiqod MEANSTACK` (first 3 months unpaid).
- 2026-11-04 — **The success heading is not reliable on internship jobs.** On all 10 submissions the dialog closed immediately and the header `Apply` button was replaced by an `Undo · 4:5x` countdown toast; polling `document.body.innerText` for `Success! Your application has been sent.` never once matched (the phrase exists only for a fraction of a second, if at all). Treat `Undo · N:NN` appearing where `Apply` was as the in-page submit signal, then confirm on `/jobs/applications`. The row lands at the top of the `Ongoing` tab within ~2 s, labelled `Scheduled` while the undo window is open and flipping to `Pending` after ~5 minutes. `✓ Applied` (disabled) on the job page is still the durable proof.
- 2026-11-04 — **Screen the years bar without opening the dialog.** The job page's left meta panel renders `Experience` as plain body text; `/Job type \| [^|]+ \|[\s\S]{0,400}?Experience \| ([^|]+?) \|/` on the flattened `innerText` returns it in one pass. Only click `Apply` when the regex returns nothing or `1+ years`. This made ~120 full-time screenings cheap; the dialog is still authoritative if the page is ambiguous.
- 2026-11-04 — **The saved search's full-time pool is exhausted for this candidate.** 191 unique cards loaded (45 wheel scrolls of 309 results) produced zero eligible full-time roles: every in-lane listing was 2+, 3+, 4+ or 5+ years, including titles with no seniority prefix (`Software Engineer` at DC Tech 3+, `AI Engineer` at NTT 5+, `Junior Software Engineer` at VoiceQube 2+ again). All 10 applications came from the **Internship-only** filter.
- 2026-11-04 — **Filter mechanics:** `#form-input--jobTypes--full_time` / `--internship` are visually hidden, so Playwright `.click()` times out with "element is not visible / intercepted". Click `label[for="form-input--jobTypes--..."]` via `page.evaluate` instead, then `View results`. Internship-only gives `69 results`. Restore Full Time afterwards by the same label click (result count returned to 302, not 309 — postings churn hourly, so do not treat the delta as a bug).
- 2026-11-04 — **Do not use the header `#search` box for job search.** It autocompletes company names and pressing Enter navigates to `/search?q=...`, the global people/companies/locations search, not the job list. Use the Filters dialog or direct job URLs.
- 2026-11-04 — A handful of cards link to dead listings that render `We couldn't find this job` (4884489, 4884490, 4884491, 4748725). Treat a 404 h1 as a dead card, not a skip to report.
- 2026-11-04 — Additional unpaid/near-unpaid patterns confirmed today, all skipped: no pay range anywhere in the JD (`Anshumat Foundation`, `Recollia`, `AlwayzON`), `performance-based stipend` with no amount (`CommuSync`), `fixed learning stipend` for a non-engineering execution role (`Rothenhall Partners`). Two more external funnels: `AVYAM LABS` (careers@ email) and `Neugence` (off-site Buildathon challenge).
- 2026-11-04 — Notion rewrote `Rubrix.ai` to `[Rubrix.ai](http://Rubrix.ai)` on the first append; every later `old_str` had to be built from the freshly fetched row text, exactly as the 2026-11-03 note warned. The `.ai` suffix triggers it just like a bare `.ai` domain.
- 2026-11-05 — Second 10-application batch (~35 min) driven by a dedicated agent on the `wellfound` session while two sibling agents used other sessions on the same relay, via `browser-control execute --session wellfound`. — Sessions stayed isolated; the explicit `--session` on every call is what keeps concurrent agents apart. — Confirms the runbook is safe for parallel multi-site runs.
- 2026-11-05 — Internship filter returned **55 results** and full-time only 11 recent cards, every one at 2+ years. — All 10 applications came from internships or intern-titled postings. — The full-time pool is still structurally closed to this candidate; do not spend time re-screening it.
- 2026-11-05 — The `Undo · N:NN` countdown plus a row on `/jobs/applications` was the verification pair for all 10 again; the `Success!` heading never appeared (consistent with 2026-11-04). Parent re-checked `/jobs/applications` and found all 10 company names present.
- 2026-11-05 — `Experience | 1+ years` in the meta panel can coexist with a `0–3 years` requirement in the JD body (Ceryneian Partners `Frontend Developer`, applied successfully). — Read the body's own range before treating a `1+` bar as a near-miss; `0–3` is eligible.
- 2026-11-05 — Three park-worthy gates seen for the first time: a JD demanding a **personal sustainability initiative** in the answer (Growth For Impact), a job requiring an **edit to profile location preferences** before it accepts the application (HOOC AI), and a hard **timezone/relocation gate** (Spenza). — All parked, none invented around. — The first is a personality question, not a resume fact; never fabricate a personal anecdote to clear it.
- 2026-11-06 — The `Filters` button on `/jobs` opens an **empty dialog** (no job-type checkboxes, no `form-input--jobTypes--*` inputs) and `/jobs?job_types[]=internship` is silently ignored (still 332 results). Only ~24 cards render and `window.scrollTo(bottom)` does not append more, so the recommended list is effectively unpaginated. — Worked around it by harvesting the "Similar jobs" links on each mid-screening job page; every good candidate this run came from there. — Do not burn time on the filter dialog or query params.
- 2026-11-06 — The **location-preferences gate is common**: FactWise (Mumbai) and AM:PM Network (Mumbai) both showed `This job does not support the locations on your profile` with required `I am currently in…` / `I can relocate to…` dropdowns, and `Send application` stays disabled until they are set. Filling them edits the account's location preferences, which non-negotiable #10 forbids. — Both parked, not applied. — Remote-friendly or multi-location postings (EveoAI) and roles with no gate (EaseOps) still submit fine, so prefer remote/multi-city listings when the batch needs volume.
- 2026-11-06 — Paid internships at `1+ years` (EveoAI, EaseOps) submit cleanly and only show the soft `Improve your odds` warning, never a hard block. — Treat the warning as informational when the posting is itself an internship.
- 2026-11-07 — **Signed-in Wellfound applies one-click; no account creation, no resume upload.** The old line in Run Notes about needing an account applied only to the signed-out flow. `Apply` on the job page opens a modal with `YOUR APPLICATION`, usually a single free-text question (`What interests you about working for this company?`), and submit/cancel. Roles with no question submit instantly on the `Apply` click and the button flips to `✓ Applied`.
- 2026-11-07 — **Stable selector for the modal submit button:** `[data-test="JobApplicationModal--SubmitButton"]`, text `Send application`. It renders 1–3 s after the click, so poll for `document.querySelector('textarea')` OR that selector rather than sleeping a fixed time or reading `.ReactModal__Content` (there are several empty portal shells; the first one is always blank).
- 2026-11-07 — **Drive one tab only.** With several Wellfound job tabs open, the scripted `js()`/CDP context and the visually rendered page diverged: modals read as empty (`textContent` 0, no `textarea`, AX dialog with no children) while the screenshot clearly showed the filled dialog. Close extras via `Target.closeTarget` and keep a single page, or you will debug a phantom modal for an hour.
- 2026-11-07 — **`✓ Applied` can be months old.** Auroscale, Timbre and Quixta were applied on 2026-10-31 but sat at `Drafted` in Notion, so the click did nothing and the page simply showed its existing state. Read the date in `/jobs/applications` before recording today's timestamp.
- 2026-11-07 — **Company-level matching is not enough, again.** `Raushang4 Technology` showed an applied `AI Agent / LLM Engineer` (OCT 31) while the `Full-Stack Developer (Internship)` row was a different req with its own applied state. Key on the job URL/role, never the company.
- 2026-11-08 — **Cold-machine startup sequence:** `browser-control status` reporting `relay: stopped` is not a blocker. Run any trivial `browser-control execute --session wellfound --file <one-liner>.js`; that starts the relay, but the extension only connects while the `Profile 4` Chrome window is open (`open -na "Google Chrome" --args --profile-directory="Profile 4"`). The old session keeps its id and its page is `about:blank`; a single `page.goto` brings it back. Refs reset, so snapshot freshly after every cold start.
- 2026-11-08 — **A `Drafted` row decays fast.** 1 day after harvest, 3 of 5 drafts were unusable: `MiPrep AI` rendered "The job listing is no longer available", `BUIMB RESEARCH` said "Unpaid/ Revenue Partnership Basis", and `Parsewave` demanded an external apply at parsewave.ai/developer. Re-open and re-screen every draft at apply time; expect roughly half of a stale draft batch to die.
- 2026-11-08 — **The `Apply` click path that works today:** `page.getByRole('button', { name: 'Apply', exact: true }).first().click()` → poll every 1.5 s for `textarea` or `[data-test="JobApplicationModal--SubmitButton"]` (up to ~20 s) → `fillInput(page.getByRole('textbox').first(), answer)` → length check → click the submit selector → 7 s wait → look for `Undo · N:NN`. Both jobs today submitted cleanly on the first attempt with no `Success!` heading.
- 2026-11-09 — **`locator.fill` can time out on a textarea that exists but is not actionable.** On from a 50-role draft batch one dialog resolved the textarea and then hung for 30 s. Setting the value through the native setter and dispatching `input` landed first time: `Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set.call(el, answer); el.dispatchEvent(new Event('input',{bubbles:true}))`. Use that as the default fill and keep `fillInput` as the fallback.
- 2026-11-09 — **The location-preferences gate is back and silent.** `Daxani Technologies` and `Silstone Health` both rendered `This job does not support the locations or timezones for remote work on your profile` inside the modal with `Send application` disabled, so a plain `page.click` burns a 30 s timeout. Detect it by scanning the dialog text for `does not support the locations or timezones` right after the modal renders, then park. Both postings hire remotely only inside one state or region.
- 2026-11-09 — **Some Wellfound listings use a long multi-field form, not a single question.** `Metabase` showed `Current location*`, `LinkedIn URL*`, `WHERE ARE YOU BASED? (city, country)*` and `ONE LAST THING: What is the application code found in the browser console at https://metabase...`. Filling the interests textarea alone submits nothing and returns no toast and no `/jobs/applications` row. Screen for `Current location*` or `application code` before filling and park those unless the console code can be read.
- 2026-11-09 — **A drafted batch can be mostly ineligible.** 20 of 50 roles harvested the day before state a 2+ year minimum. Check the years bar before opening the apply modal; the harvest page is not a filtered pool.
- 2026-11-10 — **There are two different location gates and only one is answerable.** Soft: `This job does not support the locations on your profile` with an `I am currently in…` / `I can relocate to…` radio pair and a location combobox; answering `I can relocate to…` inside the modal resolves it and enables `Send application`. It unblocked 8 jobs today (FactWise, Huvo AI, Variabl, Valiance, DhronAI, Kuku, Celex, Arivihan). Hard: `<Company> is not accepting applications from your current location due to timezone or relocation constraints. If your current location is incorrect, please update your profile.` — no control inside the modal clears it, so park. It blocked 7 of 49 drafted roles today, including WafyNet, Spenza, TrueDax, Sciative, MaxHome.ai, Keyfalcon and TopGrep.
- 2026-11-10 — **How to commit the location combobox.** Click `label[for="form-input--qualification.location.action--relocate_to"]`, then focus the input with `page.evaluate` (`input[id*="locationId-input"]`, because the dot in the id breaks a CSS selector and the placeholder div intercepts a normal click), `page.keyboard.type(city)`, wait ~2 s, `ArrowDown`, `Enter`. Confirm with `input[name="qualification.location.locationId"]` being non-empty and `Send application` becoming enabled. City names must match Wellfound's list: `Gurgaon` returns 0 options while `Gurugram` resolves, and `Bengaluru` returns 0 while `Bangalore` offers `Bangalore Urban`.
- 2026-11-10 — **The `Improve your odds` warning is informational and fires on 1+ years too.** Do not cancel a submit just because it appears: text is `It seems you're outside the years of experience preferred for this role (1+ years in Engineering role)`. Only the explicit `2+` and above is a hard skip; 1+ roles submitted cleanly all day (Quixta, Navtech RN, Kylient, Spotsure, Decipher, Cube, taqtics).
- 2026-11-10 — **A disabled `Apply` button is the closed/external signal.** WeKnow Group's Frontend page rendered with no Apply control at all (empty button list after 12 s of polling) and no row on `/jobs/applications`; the earlier false "already applied" read came from matching the header's `Applied` nav tab. Match the button text exactly (`Apply`, `Apply now`, `✓ Applied`) and wait for it to render before deciding.
- 2026-11-10 — **A batch that throws can still have submitted.** One execute aborted on a 15 s Playwright timeout against a disabled button and returned no array, yet three of its jobs (Modstack, Silstone, RecordBook) were already `Pending` on `/jobs/applications`. Wrap each job in try/catch so one failure does not discard the other results, and reconcile against `/jobs/applications` before reporting anything as not applied.
- 2026-11-09 — **The harvest page is deleted once the batch is done.** After this run the user asked for the `9 Nov 2026` page to be cleared. It went to Trash, and the Wellfound table stayed the single record of what was actually submitted. Never treat a draft page as the audit trail; the site table plus the ledger are the audit trail.
