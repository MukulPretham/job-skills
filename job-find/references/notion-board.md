# Notion Board — Job Applications (job-find view)

The board is a page hierarchy, not a database. It is **flat: there is no date layer**. Every site has exactly one page, and that page holds one application table covering every date.

```
Job Applications                (page 40d3109c-a531-8132-847b-e945a98a70a1, 💼)
├── Wellfound                   (4113109c-a531-8184-a738-c2ff22575c43, 🟢)
├── Hiring Cafe                 (4113109c-a531-819982a1d2e3afb220bb, ☕)
├── Indeed                      (4113109c-a531-8134-853b-eaf20c74551d, 🔵)
├── Cutshort                    (4123109c-a531-818680e6c4559b436dc0)
├── Apna                        (4123109c-a531-817bab87cf1614cd2a02)
├── Shine                       (4123109c-a531-81acaa28dabc12cd3454)
├── Hirist                      (4123109c-a531-812286a1fdb50e79d801)
├── Run Notes                   (4113109c-a531-81a5-93b9-f1c654ae58c0, 📝)
└── Hyderabad Outreach          (4113109c-a531-810b-9468-ca04e63cc1d1, 🤝)
```

- `Run Notes` and `Hyderabad Outreach` are **not** application pages. Never add a job row to either.
- Expect new site pages later. Always fetch the root and enumerate its children instead of trusting this list.
- Search results are polluted: a search for a site name also returns `Run Notes`, whose body mentions every site. Resolve a site page by walking the root's children and matching the child title, not by taking the first search hit.

## 1. Resolve the root

```js
const res = await tools.notion["notion-search"]({
  query: "Job Applications",
  page_size: 20
});
```

Pick a page whose title is exactly `Job Applications` (case-insensitive, emoji prefix allowed). Known ID: `40d3109c-a531-8132-847b-e945a98a70a1`.

Do not hijack `Student Job Application Tracker`, its `Applications` database, or any near-match. If the root genuinely does not exist, stop and ask the user; do not create a second root silently.

## 2. Resolve the site page

```js
const root = await tools.notion["notion-fetch"]({ id: rootPageId });
```

Walk the `<page url="...">Title</page>` children. Match the canonical site title case-insensitively, ignoring emoji prefixes and punctuation. Accept `Well Found` / `well found` as `Wellfound`.

If more than one child matches, stop and ask which one to use. Never merge or delete pages on your own.

## 3. Create a missing site page

The user's instruction: when the requested site has no page under `Job Applications`, add one that represents that site. Create it as a **direct child of the root** with the table already present.

```js
const created = await tools.notion["notion-create-pages"]({
  parent: { page_id: rootPageId },
  pages: [{
    properties: { title: "<Canonical Site>" },
    icon: "🏢",
    content: `## Applications

| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |
| --- | --- | --- | --- | --- | --- | --- |`
  }]
});
```

Then:

1. Fetch the new page and confirm the title and the 7-column header are present.
2. Confirm the root now lists it as a child.
3. Tell the user: `Created Job Applications -> <Site>.`
4. If the create call returns success but the fetch does not show the page, treat it as failed and report it. Do not create again in a loop.

Never create a site page on a hunch. Only create the site the user named in this run.

## 4. Read the existing rows

```js
const page = await tools.notion["notion-fetch"]({ id: sitePageId });
```

The content is markdown-ish. Parse every line that starts with `| ` and ends with ` |` after the separator. Skip the header and the `| --- |` separator.

Also parse **escaped rows**: some older pages (Shine, Hirist) store data rows as one paragraph of `\| cell \| cell \| ... \|` separated by `<br />`, under an otherwise empty table. Treat those as real rows for duplicate detection and reporting, even though they are not proper table rows.

For each row capture: company, role, salary, YOE, status, applied-at, link. Normalise only for comparison: lowercase, collapse whitespace, strip markdown links to their URL, strip trailing slash and query string from a URL when comparing. Keep the original text for any rewrite.

## 5. Table format

Exactly this header:

```
| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |
| --- | --- | --- | --- | --- | --- | --- |
```

A drafted row:

```
| Acme Corp | Backend Developer | ₹6,00,000/yr | 1+ yr | Drafted | 2026-11-11 (drafted) | [Job](https://in.indeed.com/viewjob?jk=abc123) |
```

- **Company**: plain text. Escape a literal `|` as `\|`. Do not wrap a bare domain unless you have to; Notion may auto-link it and rewrite the text later.
- **Role**: the title the site showed, in one line.
- **Salary**: exactly as posted. If none is posted, use `Not listed`, or `Not disclosed` where that page's existing rows use it.
- **YOE Required**: `Fresher`, `0-1 yr`, `0-2 yr`, `0-3 yr`, `0-4 yr`, `1+ yr`, `Intern`, or `Not stated`. Match the local style if the column already uses `0 yr` / `1 yr`.
- **Status**: `Drafted` for every row this skill writes.
- **Applied At (IST)**: `YYYY-MM-DD (drafted)`.
- **Link**: `[Job](url)` pointing at the live listing you opened.

## 6. Append a row

**Log one row per screened listing, immediately.** Do not hold the batch in memory and write once at the end.

1. Fetch the site page fresh. Notion rewrites bare domains and escapes characters (`_`, `$`), so a remembered string will not match.
2. Find the canonical `## Applications` table and its last real row.
3. If the table has no real data rows (only header + separator), anchor on the separator line and append the new row after it.
4. Otherwise anchor on the **tail of the last real row**, not on its company or salary cell, because those are the cells Notion rewrites. The tail is `| <YOE> | <Status> | <Applied At> | [Job](<url>) |`.
5. Compose `old_str` as that exact tail and `new_str` as the same tail plus `\n` plus the new row.
6. Call:

```js
await tools.notion["notion-update-page"]({
  page_id: sitePageId,
  command: "update_content",
  content_updates: [{
    old_str: "<exact existing tail>",
    new_str: "<exact existing tail>\n| new | row | ... |"
  }]
});
```

7. If `old_str` matches nothing, fetch again and retry once with the freshly fetched text.
8. If it still fails, do **not** blind-write. Report the row as unsaved and keep it in the run list. A `replace_content` rebuild is allowed only when the page contains just the generated heading and table; if it would delete child pages or extra sections, stop and ask.

## 7. Malformed or multi-table pages

Current known cases:

- **Shine** has an empty table whose data rows are escaped paragraph text, plus a second dated table (`## 11 Nov 2026 — applications sent`).
- **Hirist** has the same escaped-row shape.
- **Apna** has an empty table.

Rules:

- Never mass-rewrite historical rows to "fix" the table. The user owns that data.
- Duplicate-check against the whole page text, including escaped rows and the second table.
- Append new rows to the canonical `## Applications` table. If that table is empty, append after its separator; the new row becomes the table's first real row. Older escaped rows remain visible below.
- Do not append into a dated second table. If the canonical table is missing entirely, stop and ask before creating one.

## 8. Dedupe keys

A listing is already known when any of these matches:

- Same normalised company + same normalised role on this site page, in any status.
- Same normalised job URL on this site page.
- Same normalised job URL on another site page (cross-site duplicate).
- `python3 ../job-apply/scripts/ledger.py check --site "<Site>" --company "<Company>" --role "<Role>" --url "<url>"` returns `"match": true`.

Company alone is not a key. Several companies legitimately have two roles.

## 9. Failure handling

| Symptom | Action |
|---|---|
| `notion-search` or `notion-fetch` unreachable | Tell the user before searching. Do not run a browser-only harvest that cannot be saved. |
| Root missing | Stop and ask. Do not create a second root. |
| Site page missing | Create it once, then verify. |
| Permission denied | The page may belong to another workspace/connection. Ask the user to share it; do not create a replacement. |
| `update_content` matched nothing | Re-fetch, rebuild the anchor, retry once. Then report unsaved. |
| Table shorter than expected | Re-fetch before writing. Never rebuild from a partial table. |
| `replace_content` would delete child content | Stop and ask. Never pass `allow_deleting_content: true` without explicit confirmation. |
| Write returned success but the row is absent on re-fetch | Wait a moment, re-fetch once. If still absent, treat as failed and say so. |

Never claim a row was saved because the API returned success. The verification fetch is the proof.
