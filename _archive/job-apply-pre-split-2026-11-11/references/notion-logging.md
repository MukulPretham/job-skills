# Notion Logging — Job Applications

The user wants a fixed page hierarchy, not an ad-hoc database. Since **2026-11-07 the
hierarchy is flat — there is no date layer** (the user restructured it; the day pages
11-03 → 11-06 and their 11 per-day site pages are archived):

```
Job Applications                (page 40d3109c-a531-8132-847b-e945a98a70a1, icon 💼)
├── Wellfound                   (page 4113109c-a531-8184-a738-c2ff22575c43, 🟢)
│   └── one table, every date merged
├── Hiring Cafe                 (page 4113109c-a531-819982a1d2e3afb220bb, ☕)
│   └── one table, every date merged
├── Indeed                      (page 4113109c-a531-8134-853b-eaf20c74551d, 🔵)
│   └── one table, every date merged
├── Run Notes                   (page 4113109c-a531-81a5-93b9-f1c654ae58c0, 📝)
└── Hyderabad Outreach          (page 4113109c-a531-810b-9468-ca04e63cc1d1, 🤝)
```

Each site page contains **exactly one table**, `## Applications`, with one row per
application. `Applied At (IST)` carries the date — that is why the date layer was
removed. Never create a date page, a second table, a page per application, or a
database.

`Run Notes` is a **single consolidated log**, newest entry first — every session
produces observations that do not belong in an application row (verification
deviations, skip counts, parked jobs, flags, skill updates). Append a new
`## YYYY-MM-DD — <title>` section at the top; never create one per date or per site.

`Hyderabad Outreach` is a different animal — people, verified published emails,
outreach templates, and a log of what was sent. It holds **no applications**. Do not
add job rows there and do not read it as an applied set.

Baseline row counts (2026-11-07), to catch a truncated fetch: Wellfound 52
(32 `Applied` + 20 `Drafted`), Indeed 18, Hiring Cafe 21.

Before writing any Notion content, read the markdown specification through the MCP
resource interface:

```
tools.opencode.read_mcp_resource({
  server: "notion",
  uri: "notion://docs/notion-flavored-markdown-spec"
})
```

Do not guess table syntax or mention syntax.

## 1. Confirm the IST date

Run:

```sh
python3 <skill-dir>/scripts/ist_now.py
```

or:

```sh
TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M %Z'
```

Use `YYYY-MM-DD HH:MM IST` for the `Applied At` cell, captured at verification time.
That cell is the only place a date appears in an application, so a run crossing
midnight IST simply writes two timestamps — there is nothing to split.

## 2. Resolve the root page

Search:

```js
const res = await tools.notion["notion-search"]({
  query: "Job Applications",
  page_size: 20
});
return res;
```

Pick a result whose title is exactly `Job Applications` (case-insensitive, emoji
prefix allowed) and whose type is a page. Known ID:
`40d3109c-a531-8132-847b-e945a98a70a1`.

**Near matches are not the destination.** A search may surface a template such as
`Student Job Application Tracker` or an `Applications` database, and a search for a
site name also surfaces `Run Notes`, whose markdown contains a table of the same
shape. Do not hijack, edit, or restructure the template; do not write applications
into `Run Notes`. Walk the children of the known root instead of trusting search
order.

Create the root only if it genuinely does not exist:

```js
const created = await tools.notion["notion-create-pages"]({
  pages: [{
    properties: { title: "Job Applications" },
    icon: "💼"
  }],
  creation_mode: "draft"
});
return created;
```

Then tell the user it is private and offer to move it. Do not move or share it
without direction.

## 3. There is no date page

Do not create one, and do not create one "just for today's run". If something
convinces you a date page is needed, stop and ask the user — the flat layout is a
deliberate choice, not an omission.

### 3a. Harvest and draft pages are temporary

A page titled `Draft — <date>` or `<n> <Month> <year>` under the root is a working
queue of harvested roles parked at `Drafted`, not part of the fixed hierarchy. Rules:

- Applications never go in one. The site table is the only application record, and a
  submission is written there, never on the harvest page.
- Treat every row on a harvest page as unverified. Re-screen it at apply time; roughly
  half a stale harvest is unusable (2026-11-08) and a large share may state 2+ years
  (2026-11-09).
- When the batch is finished, the user considers the page spent. Delete it to Trash
  with `notion-delete-pages` and `user_confirmed: true` once he asks, then confirm the
  root page no longer lists it. Do not keep it as an archive and do not restructure it
  into a table of outcomes.
- Never delete it on your own initiative; wait for the instruction.

## 4. Resolve the site page

Canonical titles and IDs:

| Site | Page title | Page ID |
|---|---|---|
| Indeed | `Indeed` | `4113109c-a531-8134-853b-eaf20c74551d` |
| Wellfound | `Wellfound` | `4113109c-a531-8184-a738-c2ff22575c43` |
| Hiring Cafe | `Hiring Cafe` | `4113109c-a531-819982a1d2e3afb220bb` |

Fetch the root page and look for a child page with the canonical title. Match
case-insensitively, ignore the emoji prefix, and accept obvious aliases
(`Well Found`, `well found`) so you never create a duplicate.

```js
const root = await tools.notion["notion-fetch"]({ id: rootPageId });
return root;
```

The site page always exists now, so creation should never happen. If it truly is
absent, create it as a **direct child of the root** (not of a date page), with the
table already in its content:

```js
const sitePage = await tools.notion["notion-create-pages"]({
  parent: { page_id: rootPageId },
  pages: [{
    properties: { title: "Indeed" },
    icon: "🏢",
    content: `## Applications

| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |
| --- | --- | --- | --- | --- | --- | --- |`
  }]
});
return sitePage;
```

If the site page exists but has no table, add one with `insert_content` at the end.
Insert the heading only if the page does not already have an `## Applications`
heading; otherwise insert just the table, so you do not end up with two headings:

```js
await tools.notion["notion-update-page"]({
  page_id: sitePageId,
  command: "insert_content",
  position: { type: "end" },
  content: `| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |
| --- | --- | --- | --- | --- | --- | --- |`
});
```

If the site page already has a table with these columns, never add a second one.

## 4a. The Run Notes page

One `Run Notes` page for the whole workspace, a direct child of the root. **One write
per run**: after the last verified application, or when stopping early. It is the
durable version of the chat report's non-tabular half.

Newest first. Insert a new top-level section above the previous entry:

```
## YYYY-MM-DD — <short title>
<b>Restructure.</b> / <b>Harvest.</b> style bold lead-ins are fine; the live page uses them.

| Site | Requested | Verified | Skipped | Parked |
| --- | --- | --- | --- | --- |

**Pool:** <filter/query used, how many candidates opened>
**Key finding:** <structural facts, e.g. the pool is exhausted for this seniority>
**Verification:** <the surface that actually confirmed, and any deviation from the runbook>
**Skips (<n>):** <counts grouped by reason>
**Needs an answer:** <company, role, exact question, URL>
**Parked for manual action:** <captcha / login / ATS block, with URL>
**Flag for the user:** <below-baseline pay, residency gates, anything the user should overrule>

## Incidents
<session leaks, bot walls, tab churn, three-strike stops — with the fix used>

## Skill updates from this run
<which reference files changed and what they gained>
```

Rules:

- **Never put applications here.** Rows live in the site tables; this page refers to
  them by name only.
- **Never leave a run unmentioned.** A run with zero submissions still gets a
  section saying so and why.
- Do not create a second `Run Notes` page for a later run on the same day — append
  to the existing one.
- Do not edit this page mid-run; one write at the end avoids half-written notes.

## 5. Table format

Header and separator, exactly:

```
| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |
| --- | --- | --- | --- | --- | --- | --- |
```

Rows:

```
| Acme Corp | Backend Developer | ₹6,00,000/yr | 1+ yr | Applied | 2026-11-03 14:32 IST | [View job](https://in.indeed.com/viewjob?jk=abc123) |
```

Rules:
- **Company:** plain text. Escape a literal `|` as `\|`. Keep it one line. Existing
  rows sometimes link the company (`[red6.ai](http://red6.ai)`) — match the local
  style, do not rewrite old rows.
- **Role:** plain text. Use the title the site showed.
- **Salary:** exactly as posted (`₹6,00,000/yr`, `₹25,000/mo`, `₹1,500/day`). If none: `Not listed`. Do not convert or invent.
- **YOE Required:** `Fresher`, `0-1 yr`, `0-2 yr`, `1+ yr`, or `Not stated`. Use `2+ yr` only when the user explicitly overrides the fresher gate. Otherwise prefer the most specific number the JD gave. (`0-2 yr` was added on 2026-11-03 for Hiring Cafe, which posts many genuine `0-2 years` roles that the older enum could not represent honestly.) Live rows also carry bare `0 yr` / `1 yr` — keep the column's existing style rather than normalising it.
- **Status:** see §5a.
- **Applied At (IST):** `YYYY-MM-DD HH:MM IST`, at verification time. `Drafted` rows use `YYYY-MM-DD (drafted)`.
- **Link:** `[View job](url)`. If the URL contains `|`, percent-encode it.
- Keep cells inline. Use `<br />` if a cell truly needs a line break.

## 5a. Status values

| Status | Meaning |
|---|---|
| `Drafted` | Harvested and queued, **not submitted**. Not an application. |
| `Applied` | Submission verified on the site's own confirmation surface |
| `In Progress` | Site shows the application as under review |
| `Interview` | Interview invite/scheduling |
| `Offer` | Offer received |
| `Rejected` | Explicit rejection |
| `Withdrawn` | User withdrew |

`Drafted` was introduced by the 2026-11-07 Wellfound harvest: 20 roles were collected
and confirmed live but deliberately not submitted. Promote a `Drafted` row to `Applied`
**only** with a verified submission — never because a run "probably applied". Leave it
at `Drafted` and add the verified row only if the same company+role was submitted
through another channel, otherwise the duplicate gate breaks.

## 6. Append a verified application

**Log one row per verified application, immediately.** Do not wait until the end of the batch. The user confirmed this on 2026-11-03: after the site's confirmation surface verifies a submission, write the row to Notion before starting the next job.

Then:

1. Fetch the site page (its one table covers every date).
2. Extract the existing table block. It starts at the header row and continues through the last row.
3. If the fetched table contains an empty placeholder row (Notion sometimes renders one), omit it when composing the new table.
4. Compose the new table by appending one row.
5. Update with a targeted replacement:

```js
await tools.notion["notion-update-page"]({
  page_id: sitePageId,
  command: "update_content",
  content_updates: [{
    old_str: "<exact existing table block>",
    new_str: "<existing table block plus the new row>"
  }]
});
```

6. If the tool reports that `old_str` matched nothing, fetch again and retry once with the freshly fetched table text. If it still fails, fall back to `replace_content` with the full page body (heading + table). The site page should contain only that generated content.

```js
await tools.notion["notion-update-page"]({
  page_id: sitePageId,
  command: "replace_content",
  new_str: `## Applications

| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |
| --- | --- | --- | --- | --- | --- | --- |
| ... |
| ... |`
});
```

Do **not** pass `allow_deleting_content: true` silently. If `replace_content` reports that child pages/databases would be deleted, stop, show the list to the user, and ask before retrying. This should not happen if the site page only contains the generated table; extra content means someone edited it.

7. Verify by fetching the site page again and confirming the new row is present. A successful API call is not proof; the fetched markdown is.

If the same company+role already has a row on that site, do not add a duplicate.
Match on **company + role**, never company alone — several companies have two rows
(Rubrik ×2, Nimble Solutions ×2, red6.ai ×2). Update the existing row instead and
tell the user.

## 7. Update a status later

When the user says "mark <company> as rejected/interview/offer" or "update my application status":

1. Ask which site only if the match is ambiguous; there is no date to ask for.
2. Find the row:
   - Fetch each candidate site page (three fetches at most) and search for the
     company/role in its table.
   - `notion-search` with the company name can also surface the page; use it as a hint, then confirm in the fetched table. Ignore `Run Notes` hits.
3. If more than one row matches, list the matches (site, company, role, applied-at, current status) and ask which one.
4. Replace only that row's `Status` cell. Keep the other cells byte-for-byte identical.
5. Use the same `update_content` old-table → new-table approach, then fetch and verify.
6. Do not rewrite unrelated rows or pages.

## 8. Failure handling

| Symptom | What to do |
|---|---|
| `notion-search` unavailable or errors | Tell the user before applying. If they still want the run, keep the local ledger and log Notion later. |
| Root or site page missing | Stop and ask. The pages are user-owned and pre-existing; recreate only on explicit instruction. |
| Permission denied on a page | The page may belong to another workspace/connection. Ask the user to share it with the integration or choose another parent. |
| `update_content` warns that `old_str` matched nothing | Fetch the page again, rebuild the table text from the live fetch, retry once. Then use `replace_content`. |
| Table far shorter than baseline counts | The page was restructured or the fetch was truncated — re-fetch before writing, and never rebuild from a partial table. |
| `replace_content` lists child content to delete | Stop and ask. Never use `allow_deleting_content: true` without confirmation. |
| Duplicate site page suspected | Fetch the root and compare child titles before writing. If duplicates already exist, ask which one to use; do not merge or delete on your own. |
| Notion write succeeds but fetch does not show the row | Wait a moment and fetch again (async indexing). If still missing, treat it as failed and keep the ledger entry. |

## 9. What to report

Include in the final chat report:
- The exact hierarchy path, for example `Job Applications → Indeed` (no date node).
- The Notion page URL if the tool returned one.
- The `Run Notes` URL plus one line naming what the entry recorded.
- The IST timestamp(s) used in `Applied At`.
- The number of rows written and verified.
- Any row that failed to write, with the ledger fallback noted.
