# Cutshort — Site Runbook

**Scope:** this run applies on `cutshort.io` only. Cutshort hosts the whole flow on site (intro message → recruiter questionnaire → chat), so no external ATS appears in the normal path.

Site name in Notion: **Cutshort**.

## 1. Golden rules

1. **Login is mandatory and already present** in the user's Chrome profile (`mukulpretham@gmail.com`, candidate "Mukul Pretham"). Never type credentials; if the page lands on login, stop and ask the user to sign in.
2. **Only `/profile/*` URLs exist.** `/messages`, `/dashboard`, `/inbox` are hard 404s ("We tried hard but could not find your page"). Do not guess them.
3. **"Messages = 0" is normal.** The Messages tab counts *recruiter conversations with unread replies*. Recruiter screening questionnaires arrive on the **applications** side (`stage=awaiting`) and do not show there. Judge activity from the dashboard counters and the pending list, not from the Messages tab.
4. Every application is an **outbound intro message** you write on the job page. That message is the application; the questionnaire is the employer's reply to it.
5. A questionnaire that renders a **`Submit` button** is unanswered, even if options look pre-marked. A submitted one is replaced by the text `Questionnaire submitted!`.
6. Submitting is **irreversible**: the site warns "Responses cannot be changed after submission". Read the questions, decide the answers, then submit once. Never re-submit or guess.
7. The site is Cloudflare Turnstile fronted. Its console CSP errors (`Connecting to 'data:,' violates...`, `No available adapters`) are **benign noise**, not failures.

## 2. Setup and session

- Browser Control session: `cutshort` (`session_new({ id: "cutshort" })`).
- The extension only connects while that Chrome window is open. If `execute` reports `extension is not connected` after Chrome was closed, run `open -a "Google Chrome"`, wait ~10 s, then retry — the relay autostarts on the next operational call. `browser-control status --json` is the check (`extension.connected`, `activeTargets`).
- Losing the window mid-run shows up as `Target page, context or browser has been closed`. Reconnect, then re-read state; nothing already submitted is lost.

## 3. Quick reference: URLs and selectors

| Thing | Value |
|---|---|
| Landing → redirects to | `https://cutshort.io/profile/candidate-dashboard` |
| Dashboard counters | "Conversations with companies", "Applications pending / shortlisted / rejected" |
| Messages (unread conversations) | `/profile/candidate-conversations?stage=unread` |
| Pending applications | `/profile/candidate-conversations?i=all&stage=awaiting` |
| Shortlisted | `/profile/candidate-conversations?i=all` |
| Rejected / closed | `/profile/candidate-conversations?i=all&stage=nottakenforward` |
| One thread | append `&thread=<24-hex-id>` |
| Message composer | `textarea[placeholder="Type your message..."]` + `button` "Send" |
| Questionnaire form | `form > ol > li > fieldset` with the question in `legend` |
| Questionnaire option | `div[tabindex="0"]` inside the fieldset (custom radio, no `<input>`) |
| Questionnaire submit | `button[type=submit]` (its text is `Submit`) |

Logged-in signal: the left rail renders `Dashboard / View jobs / Messages / Plans / Credits / Settings` and the talent card shows the user's name. Logged-out signal: the marketing home page with `Find jobs / Hire talent`.

## 4. Reading the queue

1. Open `?i=all&stage=awaiting`. Header reads `Employer actions on your <N> applications` with tabs `Pending <N> / Shortlisted / Closed`.
2. **Rows are plain divs, not links** — there are no `href`s to scrape. Clicking a row pushes `&thread=<id>` into the URL, so the cheapest way to get thread ids is to click each row in a loop and record `page.url()` after each click.
3. The list **renders only 8 rows** even when the counter says 13 (virtualised/limited). Scrolling the wheel does not load more. Report the counter as the application count and the rendered rows as the thread count; do not claim the missing ones were read.
4. Each row shows `Company`, `For job <title>`, a relative timestamp, and a tag `[Questionnaire]` meaning the employer sent screening questions.

## 5. Reading one thread

Navigate straight to the thread URL and read body text after the marker `View full job description`. A thread contains, in order:

- job header (title, company, location, experience band, `₹X – ₹Y/yr` or `/mo`, skill chips)
- **your** intro message with a timestamp
- the recruiter's reply (recruiter name, then a thank-you line + the questions)
- either the live form or `Questionnaire submitted!`
- `Attach resume / Attach document / Send / Got hired / Archive`
- a recruiter-activity line, e.g. `The recruiter was last active on this job 5 days ago`

Detect state with a substring test, not markup:

```js
const t = await page.evaluate(() => document.body.innerText);
const answered = t.includes('Questionnaire submitted');
```

## 6. Answering a questionnaire

Questions seen so far are always the same three shapes: **location OK?**, **official notice period?**, **does the pay work?**. Options are fixed strings:

| Question | Option to pick |
|---|---|
| Location on site (Bengaluru, Mohali, Indore, …) | `I am not in this location but can relocate` |
| Location is remote | `I am currently in this location and okay with it` |
| Notice period | `Served notice, available immediately` |
| Pay works | `Yes, this works` (only when pay clears the floor in `candidate-profile.md`) |

Options are styled-component divs, so `getByText(label, { exact: true }).click()` is the stable interaction. **Selection is not visible in the clicked element's own class** — the state lives on the option's first child indicator:

```js
// returns the label of the selected option in each fieldset
const state = await page.evaluate(() => {
  const out = [];
  document.querySelectorAll('fieldset').forEach(fs => {
    const q = fs.querySelector('legend')?.innerText.trim();
    let picked = null;
    fs.querySelectorAll('div[tabindex="0"]').forEach(el => {
      const ind = el.querySelector(':scope > div');
      if (ind && ind.className.includes('eMTsng')) picked = el.innerText.trim();
    });
    out.push({ q, picked });
  });
  return out;
});
```

`eMTsng` is a minified class and will rotate on any redeploy. If it stops matching, generalise to "indicator child is non-empty / has a child node" rather than hard-coding a new hash.

Submit sequence, and the only acceptable success proof:

```js
await page.locator('button[type=submit]').first().click();
// confirm dialog: "Responses cannot be changed after submission. Are you sure?"
await page.getByText('Yes', { exact: true }).first().click();
// verify: body contains "Questionnaire submitted!" AND console shows
// [Track] Submitted screening answers successfully {jobid: ...}
```

Confirm the dialog text matches the approved action before accepting it. Then re-open the thread (fresh `goto`) and re-test the `Questionnaire submitted` substring — never trust the optimistic DOM alone.

## 7. Sending a follow-up message

Composer is `textarea[placeholder="Type your message..."]`; send with the button named exactly `Send`.

```js
const ta = page.getByPlaceholder('Type your message...');
await ta.click();
await ta.fill(msg);
await page.getByRole('button', { name: 'Send', exact: true }).click();
```

Verify by reloading the thread and finding the message text with a fresh timestamp.

**Tone rule (user directive):** write like a human sending a cold message. Plain sentences, no em dashes, no `--` separators, no bullet lists, no corporate filler. Short: 2–3 sentences, name the recruiter, say the thing (answers submitted, available immediately, open to a call), sign off with the first name. Example accepted by the user:

> Hi Anand, thanks for the questions. I have submitted my answers. I can join immediately and I am free for a call or a technical round whenever it suits you. Let me know what works.

## 8. Screening notes specific to this site

- The questionnaire `legend` is often the **only** place the pay band appears (`This job offers around ₹8L - ₹11L / yr`, `₹3,000 - ₹4,000 / mo`, sometimes blank). Read it before answering the pay question.
- Cutshort invites applications to roles above the lane (e.g. `L3 SDE`, `2 - 5 yrs`, `₹3L - ₹9L/yr`) that the job page itself shows. Check the band on the thread header and skip those in future runs.
- Internship pay is often monthly and far below the floor. Answering "yes pay works" there locks in a wrong commitment, so those go back to the user instead.

## 9. Pacing and failure signatures

- Page loads need ~4–6 s after `domcontentloaded` before the thread renders; 2.5 s is enough for a text-only state check on an already-warmed page.
- Each `goto` re-fires the Turnstile challenge; expect a dozen console errors per page load and ignore them.
- No visible rate limiting observed while walking 8 threads back to back.
- `locator.click: Target page, context or browser has been closed` — Chrome window closed; not a site problem.
- No `href` on list rows: any script that tries to harvest thread links will silently return zero results.

## 10. Reporting

Report per application: company, role, pay band, recruiter name, and questionnaire state (submitted / awaiting answers / skipped). Give the dashboard's pending count alongside the number of threads actually read, and say plainly when they differ.

## 11. Hard rules

- Never submit answers to a pay question the user has not approved when the band is below the floor in `candidate-profile.md`.
- Never answer a questionnaire the user marked "skip" — leaving it unsubmitted is the correct state.
- Never message a recruiter with an invented fact about the user's experience. Fresher, one 2-month internship, no professional years.
- Do not touch profile, talent card, plans, credits, or settings.

## Field notes (append-only)

- 2026-11-08 — `/messages`, `/dashboard` and `/inbox` return the cutshort 404 page; the whole candidate UI lives under `/profile/` — discovered after two wasted navigations, so never guess top-level paths again.
- 2026-11-08 — The Messages tab read `No conversations here.` while 8 recruiter questionnaires sat in `stage=awaiting`; the two surfaces are unrelated — stopped treating an empty Messages tab as "no recruiter activity".
- 2026-11-08 — Pending counter said 13 but only 8 rows rendered and wheel-scroll loaded nothing; reported both numbers instead of implying all 13 were inspected.
- 2026-11-08 — Questionnaire radios are divs with the selected state on the first child indicator (class `eMTsng`), not on the option itself; the naive class-diff check reported "no change" for three correctly selected answers and nearly caused a re-click.
- 2026-11-08 — Submitting pops "Responses cannot be changed after submission"; success proves out as body text `Questionnaire submitted!` plus console `Submitted screening answers successfully {jobid}`.
