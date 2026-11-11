# Site Search Playbook

One section per job site. Re-read the section for today's site at the start of the run. If the live page contradicts this file, trust the live page and append a field note at the bottom.

## Shared browser shape

This machine exposes the browser MCP as `browse`:

```js
const r = await tools.browse.execute({
  code: `
    await page.goto('https://example.com', { waitUntil: 'domcontentloaded', timeout: 60000 });
    return { url: page.url(), title: await page.title() };
  `
});
return r;
```

Other harnesses may expose `tools["browser-control"].execute` with the same Playwright surface. Use whichever exists. Never add an MCP server yourself.

Helpers inside `execute`:

- `page`, `context`, `browser`
- `snapshot({ find: /.../i, context: 1 })` for a compact semantic outline
- `ref("e12")` for a stable locator from the last snapshot
- `ariaSnapshot()` for full accessibility YAML
- `handoff("what the user should do")` when only a human can proceed
- `screenshotWithLabels()` if a visual check is needed

Keep one tab per site. Return `page.url()` and a short diagnostic in every call.

## Shared screening read

After opening a job page, pull the facts in one evaluate:

```js
const facts = await page.evaluate(() => {
  const text = (document.body.innerText || '').replace(/\s*\n\s*/g, ' | ');
  const years = text.match(/\b(\d{1,2}\s*(?:\+|-|–|to)\s*\d{0,2}\s*(?:years?|yrs?))\b/i);
  return {
    title: document.title,
    h1: (document.querySelector('h1')?.innerText || '').trim(),
    years: years ? years[1] : '',
    text: text.slice(0, 6000)
  };
});
return facts;
```

Look for the company name, the posted salary, the experience line, and the apply control. Then apply the rules in `SKILL.md` and `candidate-profile.md`.

## Indeed — `in.indeed.com`

**Login signal:** the header contains a link whose text includes `Sign out` and the user's email. If it shows `Sign in`, stop and hand off.

**Search:** never `page.goto()` a `/jobs?q=...` URL; it triggers Cloudflare 429. Go to `https://in.indeed.com/`, fill `input[name="q"]`, optionally `input[name="l"]`, and click `button[type="submit"]`. Enter does not submit. The resulting URL is safe because it came from the UI.

**Home shelves first:** on the signed-in home page, read `Jobs for you`, `Recommended for you`, `Because you viewed...`. Extract anchors containing `viewjob` or `jk=`. De-duplicate by `jk`. Skip keyboard-pattern junk ids (`789abcdef0123456`, `890abcdef0123456`, `a1b2c3d4e5f67890`).

**Result cards:** `div.job_seen_beacon`; the title anchor is `h2.jobTitle a, a.jcs-JobTitle, h2 a`; company `[data-testid="company-name"]`; location `[data-testid="text-location"]`; pay `.salary-snippet-container, [data-testid="attribute_snippet_testid"]`.

**Job page:** `https://in.indeed.com/viewjob?jk=<jk>` opens directly without the wall. The description starts at `Full job description` and ends at `Report job`, `Similar jobs`, or `Is there a problem with this job`. The apply control is usually an `<a>`; read its text to detect `Apply on company site`.

**Queries that produced hits:** `full stack developer`, `backend developer`, `software engineer fresher`, `mern stack developer`, `react node developer`, `python developer fresher`, `node js developer fresher`, `java developer fresher`, `software trainee fresher`, plus one `Remote` pass.

**Pacing:** 2 to 3 seconds between job pages. On 429 / `Just a moment...`, wait 45 seconds and reload once, then stop.

## Wellfound — `wellfound.com`

**Login signal:** snapshot shows a button like `Avatar for Sanku Mukul Pretham`, or the nav shows Jobs / Applied / Messages. Login / Sign up means signed out.

**Search:** `https://wellfound.com/jobs`. Use the saved-search chips and the `Filters` dialog. Job types `Full Time` and `Internship`; tick `Hide jobs which require me to apply on the company's website`. The filter inputs are visually hidden; click the `label[for="form-input--jobTypes--..."]` via `page.evaluate`.

**Cards:** anchors whose href starts `/jobs/`; anchor text carries the title and often the pay band. De-duplicate by the numeric job id in the URL.

**Job page preflight:** check for `✓ Applied`, an external-apply phrase (`apply at`, `apply by email`, `apply via`), and the meta panel's `Experience` value. The meta panel is authoritative over body text. `2+ years` is a hard skip; `1+ years` passes only when the JD invites freshers, interns, or strong projects.

**Known pool note:** the full-time pool is often structurally closed to this candidate; most eligible roles come from internships or intern-titled postings. Do not pad the list with 2+ roles because the full-time shelf is empty.

## Hiring Cafe — `hiringcafe.com`

**Login:** browsing and search need no account. Do not sign in or create one.

**Location:** the site defaults to US jobs. Set the location chip to **India** before searching.

**Search:** `https://hiringcafe.com/classic` and use the visible combobox `Job title or keyword`. The site also accepts a `searchState=<urlencoded JSON>` URL, but the UI is safer. Useful keys: `searchQuery`, `locations`, `minYoe`, `maxYoe`, `sortBy`.

**Cards:** `[data-quick-job-card]` elements. Extract the card's job link, title, company, salary, and location.

**Job page:** `https://hiringcafe.com/job/<slug>-<hash>`. The employer apply URL is embedded in the page HTML; do not click the apply button to discover it. Recognise ATS hosts: `jobs.ashbyhq.com`, `jobs.workable.com`, `ats.rippling.com`, `job-boards.greenhouse.io`, `jobs.lever.co`, `jobs.smartrecruiters.com`, `*.eightfold.ai`, `*.oraclecloud.com`.

**For this skill:** record the employer ATS URL in the Link cell when that is the real destination, and note the hiringcafe.com URL in the report. Hiring Cafe has no native apply form, so an ATS destination is expected, not a skip.

## Cutshort — `cutshort.io`

**Login:** the landing page redirects to `https://cutshort.io/profile/candidate-dashboard` when signed in. Only `/profile/*` URLs exist; top-level paths such as `/messages`, `/dashboard`, `/inbox` are 404s.

**Search:** use the candidate dashboard's recommended jobs and the site's own job feed. Do not guess top-level job-search URLs. If a search control is visible, use it through the UI.

**Cards:** rows are plain divs, not links. Clicking a row pushes `&thread=<id>` into the URL; record `page.url()` after each click. Read the job description after the marker `View full job description`.

**Note:** Cutshort is also a messaging/queue site; this skill only harvests job listings. Do not answer questionnaires or send messages here.

## Shine — `shine.com`

**Login:** the header shows the user's profile/avatar and a logout control when signed in. If it shows Login / Register, hand off.

**Search:** open `https://www.shine.com/` and use the visible keyword and location search. Do not guess parameterised URLs. Shine listings show `Experience`, `Salary`, and `Location` on the card.

**Job page:** read the full description for the years line and the apply control. Shine often has `Apply` on-site and `Apply on company site` variants; record the real URL.

**Known data issue:** the Notion `Shine` page currently has escaped paragraph rows plus a dated second table. See `notion-board.md` section 7. Do not repair history; append only to the canonical table.

## Hirist — `hirist.tech`

**Login:** the header shows the user's account menu when signed in. Hand off if it shows Login.

**Search:** open `https://www.hirist.tech/` and use the visible search. Hirist is tech-only and its cards carry `Experience`, `Salary`, `Location`, and `Skills`.

**Job page:** `https://www.hirist.tech/j/<slug>-<id>`. Read the description and the apply control. Many roles are 1–3 years; screen them out unless the JD also invites freshers or strong projects.

**Known data issue:** same escaped-row shape as Shine in Notion. Append only to the canonical table.

## Apna — `apna.co`

**Login:** the header shows the user's profile when signed in. Apna is mobile-first; the desktop site may push an app banner. Dismiss it, do not install anything.

**Search:** open `https://apna.co/` and use the visible job search. Filter by experience `Fresher` and location Hyderabad / Remote where the UI allows.

**Job page:** read the description and the apply control. Apna often has chat-based applications; this skill only records the listing, it does not chat.

## LinkedIn — `linkedin.com/jobs`

**Login:** the global nav shows the user's avatar and `My Network` / `Jobs` when signed in. If it shows `Sign in`, hand off.

**Search:** `https://www.linkedin.com/jobs/` and use the visible search box and filters. Do not scrape the logged-out public job pages; they hide the apply state.

**Cards:** the job list is virtualised; scroll and collect anchors containing `/jobs/view/`. Open each job page and read the description. `Easy Apply` is the only native flow; external apply is a skip for job-apply but is still a valid listing for job-find.

## Naukri — `naukri.com`

**Login:** the header shows the user's profile when signed in. Naukri often opens a login modal on search; dismiss it only if already signed in, otherwise hand off.

**Search:** `https://www.naukri.com/` and use the visible search. Naukri cards carry experience and salary. Many listings are mass recruiter ads; apply the low-quality rules.

## Any other site

Follow `new-site-recon.md`. Do not freestyle a search on a site with no section here and no recon pass. The recon produces a short site section, which you append here before writing rows.

## Field notes (append-only)

Add a dated line when a selector, URL, filter, or login signal changes.

- 2026-11-11 — Playbook created for the split `job-find` skill. Existing Indeed, Wellfound, Hiring Cafe, and Cutshort knowledge was carried over from the previous `job-apply` runbooks. Shine, Hirist, Apna, LinkedIn, and Naukri sections are first-pass maps, not yet validated by a live run; treat their selectors as hints and trust the rendered page.
