# Indeed (in.indeed.com) — Site Runbook

**Scope:** this run applies on `in.indeed.com` only. Do not open Wellfound or any other job board while this reference is active.

This is the accumulated knowledge from a real run on the user's logged-in profile. Follow it; it exists to stop you rediscovering the site's quirks the hard way. Re-read it at the start of every Indeed run. If the live page contradicts it, trust the live page and append a field note at the bottom.

## 0. The loop that works

1. Read `~/Desktop/resume.md` and `references/candidate-profile.md`.
2. Load `https://in.indeed.com/`; the user is already logged in in the shared browser profile.
3. **Work the home page recommendations first.** The signed-in home page already renders personalised shelves ("Jobs for you", "Recommended for you", "Because you viewed…"). Screen and apply from those before typing any search. Only move to search when the shelves are exhausted or none of the recommended roles are eligible. See §3a.
4. Search **through the site's UI** (fill `input[name="q"]`, click `button[type="submit"]`). **Never `page.goto()` a `/jobs?...` URL with query params** — that triggers Cloudflare 429 / "Additional Verification Required".
4. Screen candidates by opening `https://in.indeed.com/viewjob?jk=<jk>` directly (safe) and reading the description for years/fresher/entry.
5. Apply only to eligible roles (see the fresher gate in `SKILL.md` and `candidate-profile.md`): 0–2 years, fresher, entry, or 1+ with fresher-friendly wording. **Never 2+ years.**
6. Walk the smart-apply flow: resume selection → questions → (demographic) → review → submit.
7. Verify the `post-apply` page says "Your application has been submitted!".
8. Record the verified application in the ledger and Notion.

## 1. Environment and tool call shape

Browser work goes through the `browser-control` MCP. Call it from Code Mode as:

```js
const r = await tools["browser-control"].execute({
  code: `
    return { url: page.url(), title: await page.title() };
  `
});
return r;
```

Key rules:
- `execute` gives you `page`, `context`, `browser`, `snapshot()`, `ref()`.
- The returned text may be a JS-ish pretty print, not strict JSON. Return plain objects/arrays and parse defensively.
- `console.log()` inside page code is captured in `logs`; ignore it unless debugging.
- Do not pass a `timeout` argument to `execute` — the schema rejects extra properties.
- Long waits inside the page are fine: `await page.waitForTimeout(45000)`.
- Keep one implicit session. Do not create extra sessions unless you need isolation.
- Always return a small diagnostic object (`url`, `title`, a body slice) so you can see where a flow broke.

Cheap sanity check:

```js
return { url: page.url(), title: await page.title() };
```

If `status` shows `activeTargets: 0`, the first `execute` creates a relay-owned tab. Existing user tabs can be adopted with `session_adopt` if you need their exact cookies/history. For Indeed, a fresh relay tab in the same browser profile is usually already logged in, so adoption is optional.

## 2. Login and identity

- Signed in as **mukulpretham@gmail.com**. Never type credentials.
- Indeed **Resume** exists and is current at `https://profile.indeed.com/resume`.
- Phone on file: `+91 90590 15626`. Location: **Hyderabad, Telangana**.
- Profile has the summary, links, work experience, education, certifications, and skills from the resume.

Verify cheaply on the homepage:

```js
const links = await page.locator('a[href*="logout"]').evaluateAll(
  els => els.map(x => x.innerText.trim())
);
return links;
// → ["Sign outmukulpretham@gmail.com"] means logged in
```

If the header shows "Sign in", **stop and ask the user to log in manually**. Do not attempt a login flow. Wait for their confirmation, then re-check.

## 3. Searching without the Cloudflare wall

### Never do this

```js
await page.goto('https://in.indeed.com/jobs?q=full+stack&l=Hyderabad&fromage=7&sort=date');
// → 429 / "Just a moment..." / "Additional Verification Required"
```

Query-param navigations get bot-flagged. Symptom: `title` becomes `'Just a moment...'`, body contains `Additional Verification Required` and a Ray ID.

### Do this

```js
await page.goto('https://in.indeed.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(1500);
await page.locator('input[name="q"]').first().fill('full stack developer');
// Optional location: input[name="l"]
await page.locator('button[type="submit"]').first().click();
await page.waitForTimeout(4500);
```

- **Enter does not submit** the search. Always click `button[type="submit"]`.
- The resulting `/jobs?q=...&l=...&from=searchOnHP&vjk=...` URL is fine because it came from the UI.
- The `l` box persists between searches. If you set it to `Remote`, later searches stay Remote. Reset it explicitly for Hyderabad.
- Filters ("Easily apply", date posted) are unreliable to click programmatically. Do not burn turns on them; screen by reading job descriptions.

### 3a. Home page recommendations come first

The user's explicit preference (2026-11-03): check the signed-in home page recommendations before searching. They are already filtered by Indeed against the stored resume, so they convert better and cost fewer navigations.

On `https://in.indeed.com/` (no query params, safe to load directly):

- Shelves appear as headings in `body.innerText()`: `Jobs for you`, `Recommended for you`, `Because you viewed …`, `Top picks for you`, `More jobs for you`.
- Each shelf is a carousel of compact cards. Extract them by walking the shelf container:

```js
const shelves = await page.locator('section, div').evaluateAll(els => {
  const out = [];
  els.forEach(e => {
    const h = e.querySelector('h2, h3');
    const t = h ? (h.innerText || '').trim() : '';
    if (!/jobs for you|recommended|because you viewed|top picks|more jobs/i.test(t)) return;
    const cards = [...e.querySelectorAll('a[href*="viewjob"], a[href*="jk="]')].map(a => {
      const href = a.getAttribute('href') || '';
      const m = href.match(/jk=([a-z0-9]+)/);
      return {
        jk: m ? m[1] : null,
        text: (a.innerText || '').trim().split(String.fromCharCode(10)).slice(0, 3)
      };
    }).filter(c => c.jk);
    if (cards.length) out.push({ shelf: t, cards });
  });
  return out;
});
```

- The carousels are lazy: only the first few cards render until you click the next arrow, and duplicated `jk` values across shelves are normal. De-duplicate by `jk`.
- Screen each recommendation exactly like a search result: `viewjob?jk=…`, read years/fresher wording, check the apply type.
- The home page also shows a `₹…/yr` salary chip in the header and its own `Jobs for you` rail; ignore the salary chip as a filter, it is not the job's posted salary.
- If the shelves are empty (new profile, logged-out-looking shell), fall through to search and note it.

### Extract result cards

```js
const cards = await page.locator('div.job_seen_beacon').evaluateAll(els => els.map(e => {
  const a = e.querySelector('h2.jobTitle a, a.jcs-JobTitle, h2 a');
  const href = a ? (a.getAttribute('href') || '') : '';
  const m = href.match(/jk=([a-z0-9]+)/);
  const co = e.querySelector('[data-testid="company-name"]');
  const lo = e.querySelector('[data-testid="text-location"]');
  const pay = e.querySelector('.salary-snippet-container, [data-testid="attribute_snippet_testid"]');
  return {
    jk: (a && a.getAttribute('data-jk')) || (m ? m[1] : null),
    title: ((a && a.innerText) || '').trim().split(String.fromCharCode(10))[0],
    company: co ? co.innerText.trim() : '',
    loc: lo ? lo.innerText.trim() : '',
    pay: pay ? pay.innerText.trim() : ''
  };
})).filter(c => c.jk);
return cards;
```

Tips:
- Inside executed code, prefer `String.fromCharCode(10)` over `'\\n'` when you build the snippet with template literals. It removes a whole class of escaping bugs.
- 16 cards per page is normal.
- Beware junk/planted `jk` values: `789abcdef0123456`, `cdef0123456789ab`, `890abcdef0123456`, `a1b2c3d4e5f67890`. If a `jk` looks like a keyboard pattern, skip it; those listings are duplicated/ghost and often have an `undefined` apply type.

## 4. Screening a job (cheap, one call for 5–8 jobs)

Open the job directly and pull only what you need. This is fast (~1 second/job) and does not trigger Cloudflare:

```js
const jks = ['be37b07c82f9f00e', '33ede2818fa1af77']; // ...
const out = [];
for (const jk of jks) {
  await page.waitForTimeout(2200); // pacing, see §8
  await page.goto('https://in.indeed.com/viewjob?jk=' + jk, {
    waitUntil: 'domcontentloaded', timeout: 60000
  });
  await page.waitForTimeout(900);
  const body = await page.locator('body').innerText();
  const i = body.indexOf('Full job description');
  let d = i >= 0 ? body.slice(i + 'Full job description'.length) : body;
  const cut = d.search(/Report job|Similar jobs|Is there a problem with this job/);
  if (cut > 0) d = d.slice(0, cut);
  const lines = d.split(String.fromCharCode(10)).map(s => s.trim()).filter(Boolean);
  const rel = lines.filter(s =>
    /(\d+\s*(\+|\u2013|-|to)\s*\d*\s*year|fresher|entry|graduate)/i.test(s)
  ).slice(0, 3);
  const btns = await page.locator('button, a').evaluateAll(els => els
    .map(e => (e.innerText || '').trim())
    .filter(t => /^apply/i.test(t) && t.length < 40));
  out.push({
    jk,
    title: (await page.title()).split(' - ')[0],
    apply: [...new Set(btns)][0],
    rel
  });
}
return out;
```

Decision rules actually used (keep them unless the user says otherwise):

| Signal in description | Verdict |
|---|---|
| "Fresher", "0–1", "0–2 years", "Entry level", "Graduate", no years at all + knowledge-based wording | Apply |
| "1+ years" **and** the JD invites freshers/interns/strong projects | Apply |
| "1+ years" in a mid-level-sounding JD | Skip |
| "2+ years", "2–3 years", "3+ years" — including "2+ preferred" | **Skip (hard)** |
| "4–6", "5–12 years", Senior/Staff/Principal/SDE II/III, "mentor junior engineers" | Skip |
| Apply button = **"Apply on company site"** | Skip by default (external ATS: Workday/Greenhouse/SmartRecruiters — new account, long forms, often email-only). Only attempt if the user explicitly says to. |
| Role not in the user's lane (Graphic Designer content under a "Software Developer" title, SAP ABAP trainee, L1/L2 support, night shift, .NET-only, PHP-only) | Skip |
| Unpaid intern / "training + placement" / Ameerpet-style ₹1.3–3.9L "full stack" listings | Skip as low quality; mention it in the report |
| Mislabeled/duplicated listing (title ≠ description) | Skip |

Always keep the **reason** for each skip so the user can override.

## 5. The apply flow — all states you will hit

`viewjob` → click the apply affordance → `smartapply.indeed.com/beta/indeedapply/form/...`

### Clicking apply

The apply control is usually an **`<a>`**, not a `<button>`:

```js
await page.getByText('Apply now', { exact: true }).first().click();
await page.waitForTimeout(7000); // the smart-apply SPA is slow
```

`page.locator('button:has-text("Apply now")')` **times out** on these pages. Use `getByText` or `a:has-text(...)`.

If the click sends you to `/beta/indeedapply/applybyapplyablejobid?...` and the page stays blank (loading script only): that flow is stuck. Go back to `viewjob?jk=...`, click apply again. A second attempt usually works. Do not debug the loader page.

### Resume selection module (`.../resume-selection-module/resume-selection`)

Two radio cards: **"Use your Indeed Resume"** (fresh, recommended) and the uploaded PDF. The `<input type="radio">` is invisible — clicking it directly hangs. Click its label/card:

```js
const us = page.locator('label:has-text("Use your Indeed Resume")').first();
if (await us.count()) await us.click({ force: true });
await page.waitForTimeout(600);
await page.getByRole('button', { name: 'Continue' }).click();
await page.waitForTimeout(5000);
// verify: page.locator('input[name="resume-selection"]:checked').getAttribute('value') === 'structured'
```

Choose the **Indeed Resume** (`structured`), not the PDF. It carries the skills/experience data employers' filters read.

### Questions module (`.../questions-module/questions/1`)

Employer screeners. Inspect them programmatically instead of screenshotting:

```js
const fields = await page.locator('input, textarea, select').evaluateAll(els => els.map(e => ({
  tag: e.tagName,
  type: e.getAttribute('type'),
  id: e.id,
  label: (document.querySelector('label[for="' + e.id + '"]')?.innerText || '').trim().slice(0, 80),
  ph: e.getAttribute('placeholder')
})));
return fields;
```

Known patterns:

- **True/False** (for example "Excellent logical, analytical and communication skills \*") → **True**. Click the label, not the hidden input.
  `await page.locator('label:has-text("True")').first().click({ force: true });`
- **"Your Current Organization \*"** → `Fresher - Student`.
- **"LinkedIn Profile \*"** → `https://linkedin.com/in/mukulpretham`.
- **"What technologies have you worked on? \*"** — rendered as radios even though it says "all technologies"; only one is allowed. Pick the most job-relevant (NodeJS for full-stack/backend roles). Tick nothing that is not on the resume (for example React Native).
- **"Available Start Date \*"** → `DD/MM/YYYY`, type into `input[placeholder="DD/MM/YYYY"]`. For "as soon as possible", use today's date in IST.
- **Demographic/consent module** → click **Agree**, then **Review your application**.
- Radio/checkbox cards: click the **label**, never the hidden input.

**Rule for blanks:** if a required field is about a fact not in the resume and not in the standing answers (expected CTC, notice period, start date, relocation, current salary, shift availability), **do not invent it**. Park the job, keep the exact question, and ask the user in one batched message at the end of the batch. Never submit with a required blank.

### Review and submit (`.../review-module`)

The module first shows **"Preparing review"** — wait 3–6 seconds, then re-read. When ready it shows "Review your application", an optional job-alert switch (leave **off** unless asked), and:

```js
await page.getByRole('button', { name: 'Submit your application' }).click();
await page.waitForTimeout(6000);
// expect url: .../form/post-apply and body: "Your application has been submitted!"
```

`"Preview what the employer sees"` shows an **"Example resume"** placeholder. That is marketing copy, not the user's resume. Do not panic, do not re-upload.

### Verify, always

```js
return {
  url: page.url(),
  ok: (await page.locator('body').innerText()).includes('has been submitted')
};
```

A click alone is not proof. Only count an application when you see the `post-apply` page.

## 6. Answers to fill without asking

Use `references/candidate-profile.md` for the full standing-answer table. The most-used Indeed values:

| Field | Value |
|---|---|
| Expected CTC | ₹4,00,000 per annum |
| Current CTC | 0 |
| Notice period | Immediate |
| Available start date | ASAP / today's date in IST |
| Total experience | 0 years (fresher), 2-month internship |
| Relocation | Yes — Hyderabad base; Remote OK |
| Current organization | `Fresher - Student` |
| LinkedIn | `https://linkedin.com/in/mukulpretham` |
| GitHub | `https://github.com/MukulPretham` |
| Resume | Indeed Resume (structured), fallback `mukul_pretham_resume_5.pdf` |
| Gender / disability / veteran | Consent only — click Agree; do not self-declare |

Ask only for genuinely new facts: shift work, bond/agreement, "years of experience in <specific tool>", security clearance, driving licence, a portfolio URL for a specific stack.

## 7. Resume → target roles

Current profile: full-stack engineer, B.Tech CSE (AI&ML) 2023–2027, CGPA 8.0, internship at Lupira (Next.js/Node/AWS SES/S3), projects in LangGraph/LLM agents, Redis queues, Docker, PostgreSQL/Prisma.

Search queries that produced usable hits: `full stack developer`, `backend developer`, `software engineer fresher`, `mern stack developer`, `react node developer`, `python developer fresher`, `software trainee fresher`, plus a Remote pass.

Strong-match keywords: MERN, Node.js + React/Next, Express, Spring Boot/Java, MongoDB/PostgreSQL, REST, Docker, AWS, LangGraph/LLM APIs, Claude Code, DSA.

Avoid: .NET-only, PHP-only, SAP/ABAP, Salesforce, L1/L2 support, night-shift ops, data/business-analyst roles.

## 8. Rate limits, pacing, failure signatures

- Indeed throttles bursts hard. Add `await page.waitForTimeout(2000–3000)` between job navigations and ~4 seconds between search and the first job.
- **429 / Cloudflare:** `title` becomes `'Just a moment...'`, body has `Additional Verification Required` + a Ray ID. Fix: `waitForTimeout(45000)`, then `page.reload({ waitUntil: 'domcontentloaded' })`. It usually clears in ~45 seconds. Do **not** hammer retries.
- `locator.click: Timeout 30000ms exceeded` on an apply button → it is an `<a>`, or the listing changed. Re-inspect `button, a` texts instead of guessing.
- `snapshot()` truncates around 80 items (`- ... truncated after 80 items`). Read `body.innerText()` slices for anything below the fold.
- `h1` / CSS-text locators can time out on a page that actually loaded (Indeed's markup churns). Prefer `body.innerText()` + regex over element-specific assertions.
- Ignore console noise: CSP `default-src` errors, `X-OneTrust-IsBot`, Apollo duplicate-ID warnings, doubleclick CSP — all benign. Filter `logs` out of your reasoning.
- If a Code Mode script dies with `SyntaxError: unexpected token` or `invalid redefinition of parameter name`, that is your own script (for example, do not name a variable `tools`), not the site.
- If an `execute` call is aborted/cancelled, the previous navigation may still be in flight. Re-run a tiny read (`page.url()`) before assuming failure.

## 9. Reporting

Follow the report shape in `SKILL.md`. For Indeed specifically, mention:
- The `My jobs → Applied` page as a verification surface.
- The confirmation email to `mukulpretham@gmail.com`.
- Any job that needed a second apply click.
- Rate limits hit and how long you waited.

## 10. Copy-paste helpers

**Open + screen N jobs:**

```js
const jks = ['...'];
const out = [];
for (const jk of jks) {
  await page.waitForTimeout(2200);
  await page.goto('https://in.indeed.com/viewjob?jk=' + jk, {
    waitUntil: 'domcontentloaded', timeout: 60000
  });
  await page.waitForTimeout(900);
  const body = await page.locator('body').innerText();
  const i = body.indexOf('Full job description');
  let d = i >= 0 ? body.slice(i + 'Full job description'.length) : body;
  const cut = d.search(/Report job|Similar jobs|Is there a problem with this job/);
  if (cut > 0) d = d.slice(0, cut);
  const btns = await page.locator('button, a').evaluateAll(els => els
    .map(e => (e.innerText || '').trim())
    .filter(t => /^apply/i.test(t) && t.length < 40));
  out.push({
    jk,
    title: (await page.title()).split(' - ')[0],
    apply: [...new Set(btns)][0],
    desc: d.replace(/\n{2,}/g, '\n').slice(0, 1200)
  });
}
return out;
```

**Apply driver (resume selection + lands on the next state):**

```js
await page.waitForTimeout(2500);
await page.goto('https://in.indeed.com/viewjob?jk=' + jk, {
  waitUntil: 'domcontentloaded', timeout: 60000
});
await page.waitForTimeout(1800);
await page.getByText('Apply now', { exact: true }).first().click();
await page.waitForTimeout(8000);
let t = (await page.locator('body').innerText()).replace(/\n{2,}/g, '\n');
if (/resume-selection/.test(page.url())) {
  const us = page.locator('label:has-text("Use your Indeed Resume")').first();
  if (await us.count()) await us.click({ force: true });
  await page.waitForTimeout(500);
  const c = page.getByRole('button', { name: 'Continue' });
  if (await c.count()) { await c.click(); await page.waitForTimeout(5000); }
  t = (await page.locator('body').innerText()).replace(/\n{2,}/g, '\n');
}
return { url: page.url(), t: t.slice(0, 1000) };
// then handle questions / review per §5
```

**Submit + verify:**

```js
await page.waitForTimeout(3000);
await page.getByRole('button', { name: 'Submit your application' }).click();
await page.waitForTimeout(6000);
return {
  url: page.url(),
  ok: (await page.locator('body').innerText()).includes('has been submitted')
};
```

## 11. Hard rules

1. Never submit an application with a required field left empty.
2. Never invent an answer to a factual question — ask the user (batch all open questions).
3. Never apply to a role whose stated minimum experience is 2+ years.
4. Never apply to external "company site" flows without explicit permission.
5. Never type credentials, create accounts, or change the profile/resume without being asked.
6. Always verify `post-apply` before reporting a submission.
7. Always keep the report honest — list skipped jobs and the reason.
8. If the user's answer changes a standing default (CTC, notice, start date), update `candidate-profile.md` and reuse it for the rest of the run.

## Field notes (append-only)

Add new observations with a date. Do not delete earlier notes; correct them with a newer note.

- 2026-11-03 — Baseline playbook imported from `~/Desktop/indeed_apply.md`. No live run performed after import.
- 2026-11-03 — First live run (5 applications, 09:24–09:55 IST). Home page `Jobs for you` rendered one shelf with 11 unique jobs; the extractor in §3a worked, but the same shelf is nested in several wrapper elements, so de-duplicate by `jk` and ignore repeated containers. Planted duplicate `jk`s are common in shelves too (`890abcdef0123456`, `f1e2d3c4b5a67890`): skip any keyboard-pattern id.
- 2026-11-03 — Many listings that look in-lane are external ATS. `Apply on company site` appeared on roughly half the screened cards (Copart, Future Nine, Webneeds, HSK, Educase, USS, SmartNet, Lumel, Texplorers). Screening the apply control before reading the whole JD saves time.
- 2026-11-03 — The demographic/consent module (`demographic-questions-module/demographic-questions/1`) renders its `Agree` checkbox **disabled** until the enterprise reCAPTCHA token arrives. The textarea `g-recaptcha-response` was empty for ~10s, then filled (2510 chars) and the checkbox became enabled. Remedy: poll `input[type="checkbox"].disabled` every 2s for up to ~25s (moving the mouse occasionally), then click the `Agree` label; the page advances to `review-module` on its own. Do not try to force the checkbox with synthetic events — it stays disabled.
- 2026-11-03 — The `applybyapplyablejobid?...` blank loader page recurred on the Nestack listing; going back to `viewjob?jk=…` and clicking Apply once more succeeded, as documented. A second attempt is enough.
- 2026-11-03 — After a successful `post-apply`, the tab can close and the session's `page` becomes `about:blank` while a stale `review-module` tab stays open. Do not reuse that stale review tab (risk of duplicate submit). Open a fresh page (`context.newPage()`) or navigate the blank page to the next `viewjob` URL.
- 2026-11-03 — Employer questions module can appear before the demographic module (`questions-module/questions/1`). The Aviso AI form used free-text inputs for years-in-SaaS, notice period in days, current/expected CTC, and US-shift willingness; all four were required. Fill by element id (`text-question-input-_r_j_`, etc. — ids are session-scoped, so re-read them each time).
- 2026-11-03 — User now requires **immediate per-application Notion logging**: write each row as soon as `post-apply` verifies, then start the next job. Rows are appended with `update_content` on the site page; verify by re-fetching before moving on.
- 2026-11-03 — Screened-and-skipped pool for reference: BigHaat (2+), Acheron (2+), Spaceinventive (3+), EBG (2–5), BeamX (2+), Techdome (5–12), Blueberry (3–7), Vivify (5+), Anteelo (3–4), CGLIA (5+), Zippr (2–4), RandomTrees (4–6), DSmart (3–7), xcube (2–6), Teamverse (2–4), EffiaSoft (3+), Recruise AI/ML (3+). The Hyderabad fresher pool is thin; most 0–2 hits come from the recommendation shelf, not keyword search.

- 2026-11-03 (evening run, 3 applications) — Browser Control page handles are the fragile part, not the site. The `indeed-apply` session's default page closed repeatedly mid-run ("Target page, context or browser has been closed"), and `session_reset` plus `session_adopt` both left a page with `innerText()` of length 0. Reliable pattern: inside every `execute`, re-acquire the page with `const p = context.pages().find(x => !x.isClosed() && x.url().includes('indeed.com')) || context.pages()[0]`, and in a screening loop re-acquire per iteration with a single `context.newPage()` retry. `session_adopt` needs `targetUrl` or `targetIndex` once more than one Indeed tab is attached.
- 2026-11-03 — `session_reset` created a fresh tab that immediately showed "Additional Verification Required" with a Ray ID. The documented remedy worked exactly: `waitForTimeout(45000)` then `reload()`, after which the tab was logged in as mukulpretham@gmail.com. Do not retry sooner.
- 2026-11-03 — The home shelf rendered 12 unique `jk`s and 11 were ineligible (4–8 yr, 2–4 yr, 2–5 yr, PHP-only, React Native-only, external ATS, or broken listings), so search was required even though §3a says shelves first. Queries that produced on-site applies: `react developer fresher`, `python developer fresher`, `node js developer fresher`. `software engineer fresher` skewed to email/company-site listings and stale posts (Navayuga dated 2021, Ethon email-only).
- 2026-11-03 — Apply can skip both the resume-selection and questions modules: SG1, Cognike, and RandomTrees each went `Apply now` → `review-module` directly, and only needed "Preparing review" to finish. SG1 hit the blank `applybyapplyablejobid` loader once; the documented second click from `viewjob` worked. Wait 6–9s on the loader before assuming it is stuck.
- 2026-11-03 — Screening signals worth trusting: a very wide salary band (₹3,37,000–₹16,40,000/yr) plus `[1, 2]` citation artifacts or "Here are some options within 30 characters:" in the body means a scraped/generated mass listing, not a real JD. Skip those even when the title and years look eligible.
- 2026-11-03 — `https://myjobs.indeed.com/applied` loads directly (no Cloudflare wall) and lists each new application as "Applied today on Indeed"; use it as the second verification surface when the `post-apply` tab has already been navigated away.
- 2026-11-05 — Parallel three-agent run (Indeed + Wellfound + Hiring Cafe, one browser-control session each): the Indeed agent produced **10 verified applications** in ~39 minutes while the other two ran concurrently. — Screened 51 listings: 27 skipped for 2+ years, 12 external `Apply on company site`, 5 mass/junk, 7 out of lane. — Ten is achievable in one batch when the query net is widened past `full stack developer` to `java developer fresher`, `python developer fresher`, `AI engineer`, `prompt engineer`, `java software engineer`.
- 2026-11-05 — `myjobs.indeed.com/applied` renders the string `Applied today on Indeed` **twice per card**, so counting that substring double-counts the batch (20 for 10 jobs). — Counted distinct `jk` values from anchors whose ancestor text contains the phrase instead: exactly 10. — Never sanity-check a batch with a raw substring count on this page.
- 2026-11-05 — Two fresher-eligible listings failed server-side: `Ziroverse Technologies` (jk `e95bd70daa4e6a98`) and `Harsham Group` (jk `3ca41ef6849cbc0b`) both returned `Something went wrong - We're unable to process the application for this job. Please contact the employer directly to apply.` — One retry each, identical error, parked rather than replayed. — This is an employer/Indeed-side failure, not throttling; a second attempt does not clear it, so park it and spend the slot elsewhere.
- 2026-11-05 — Ziroverse's `Associate Data Forward Deployed Engineer` (0-2 yr) applied fine while its `Associate AI Forward Deployed Engineer` was broken. — Judge per listing, not per company; one req can work while another on the same employer fails.
