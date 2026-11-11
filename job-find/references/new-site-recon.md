# New Site Recon

Use this when the user names a job site that has no section in `site-search-playbook.md`. Recon maps the site without applying to anything. It is read-only.

## 1. Open and orient

1. Open the site's home page in the browser MCP, in a session named `<site>-find`.
2. Take a snapshot and read the page. Identify:
   - Is the user signed in? Look for an avatar, profile menu, logout, or "My applications". Login / Register means signed out.
   - Where is the job search? A search box, a keyword field, a location field, filters, or a recommendations feed.
   - What does a job card look like? A link, a div with a title and company, a list row.
3. If signed out, stop and ask the user to log in. Do not create an account.

## 2. One search

Run one real search for `software engineer fresher` or `backend developer` in the user's location (Hyderabad) or Remote, through the UI. Do not use a guessed query-param URL.

Record:

- The search URL the UI produced.
- The selectors that find cards and titles.
- The job URL pattern.
- Any filters that matter: experience, date posted, remote, fresher.

## 3. One job page

Open the first sensible card. Record:

- The stable URL pattern.
- Where the company, role, salary, experience, and description appear.
- The apply control text: `Apply`, `Easy Apply`, `Apply on company site`, `Apply by email`.
- The login state on the job page.

Do not click apply. Do not fill anything. Do not submit.

## 4. Write the section

Append a section to `site-search-playbook.md`:

```md
## <Site> — `<domain>`

**Login signal:** ...
**Search:** ...
**Cards:** ...
**Job page:** ...
**Known quirks:** ...

- YYYY-MM-DD — first recon; which searches and pages were used.
```

Then add the site to the canonical names table in `SKILL.md` and to the options list in the two-question block if it is a site the user is likely to reuse.

## 5. Then, and only then, harvest

Return to the normal loop: search, open each listing, screen, dedupe, write `Drafted` rows.

## Hard rules

- Recon never submits, never creates an account, never changes profile settings, and never types credentials.
- A CAPTCHA or bot wall goes to the user with `handoff()`.
- If the site has no usable search and no recommendations feed, report that honestly. Do not invent a listing from a search-engine snippet.
- If the site is an aggregator with no native apply, record the employer destination URL; that is expected, not a skip.
