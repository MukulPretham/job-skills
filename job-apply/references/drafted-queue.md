# The Drafted Queue

`Drafted` is the handoff from `job-find` to `job-apply`. A drafted row is a live listing that was screened and queued, **not** an application.

## 1. Resolve the site page

Use the root `Job Applications` page (`40d3109c-a531-8132-847b-e945a98a70a1`), walk its children, and match the canonical site title. Known IDs are in `notion-logging.md`. Do not take the first search hit: `Run Notes` also matches a site-name search.

## 2. Parse every row shape

The site page can contain:

- **Real table rows** starting with `| ` and ending with ` |`
- **Escaped paragraph rows** of the form `\| company \| role \| ... \|` joined by `<br />` (current Shine and Hirist pages)
- **A second dated table** under a heading such as `## 11 Nov 2026 — applications sent`

For this skill, the canonical queue is the rows under `## Applications`. Read the escaped rows too, because a drafted listing may be sitting there. Do not apply from a dated second table unless the user points at it explicitly; report it instead.

Capture for every row:

| Field | Why |
|---|---|
| Exact original line | Needed byte-for-byte for the status update |
| Company | Matching and reporting |
| Role | Matching and reporting |
| Salary | Keep unchanged |
| YOE Required | Re-screen signal |
| Status | Select only `Drafted` |
| Applied At (IST) | Replace with the real submission time |
| Link | Open this job |

## 3. Select the queue

- Status must be exactly `Drafted` (case-insensitive, trim whitespace).
- Do not treat `Applied`, `Applied*`, `In Progress`, `Interview`, `Offer`, `Rejected`, or `Withdrawn` as queue items.
- If a row has no link, skip it and report "drafted row has no link".
- If two rows share the same company + role or the same normalised URL, keep the first, report the duplicate, and do not apply twice.
- Respect the batch size the user chose. "All drafted" means every row that survives screening, not every row on the page.

## 4. Re-screen at the moment of applying

The harvest note is not evidence about the live page. Open the link.

Leave the row at `Drafted` and skip when:

- The listing is removed, expired, or redirects to a generic jobs page.
- The live JD states a minimum of 2+ years anywhere.
- The job is unpaid, commission-only, a training-plus-placement fee, or a bond with a fee.
- The role is out of lane: QA, SDET, support, analyst, .NET-only, PHP-only, SAP/ABAP, Salesforce, senior/staff/lead/architect/manager.
- The apply flow is an external ATS the user has not authorized for this run.
- A required question needs a fact the resume and standing answers do not contain. Park it, keep the exact question, and ask in the final report.
- The site already shows an applied state. Do not resubmit. If the site shows a real application date, update the row to `Applied` with that date and flag it as "already applied before this run".

Screening rules live in `candidate-profile.md` and the site reference. The short version: fresher, 0 to 2 years, entry level, or a 1+ role that explicitly welcomes freshers or strong projects.

## 5. Flip `Drafted` to `Applied`

Do this immediately after the site verifies the submission, before opening the next job.

The row changes in exactly two cells:

```
Status:             Drafted  ->  Applied
Applied At (IST):   YYYY-MM-DD (drafted)  ->  YYYY-MM-DD HH:MM IST
```

Everything else stays identical, including salary formatting, escaped underscores, and the link text.

### Real table row

```js
await tools.notion["notion-update-page"]({
  page_id: sitePageId,
  command: "update_content",
  content_updates: [{
    old_str: "| Acme Corp | Backend Developer | ₹6,00,000/yr | 1+ yr | Drafted | 2026-11-11 (drafted) | [Job](https://...) |",
    new_str: "| Acme Corp | Backend Developer | ₹6,00,000/yr | 1+ yr | Applied | 2026-11-11 15:42 IST | [Job](https://...) |"
  }]
});
```

### Escaped paragraph row

Replace only the escaped line fragment, keeping the surrounding `<br />` structure:

```js
old_str: "\\| Acme Corp \\| Backend Developer \\| ... \\| Drafted \\| 2026-11-11 (drafted) \\| [Job](https://...) \\|"
new_str: "\\| Acme Corp \\| Backend Developer \\| ... \\| Applied \\| 2026-11-11 15:42 IST \\| [Job](https://...) \\|"
```

Build both strings from the fresh fetch, not from memory. Notion rewrites bare domains, escapes `_` and `$`, and may change the order of inline marks.

### Verify

Fetch the page again. Confirm:

- The target row now reads `Applied`.
- The timestamp matches the IST time of the verified submission.
- No other row changed.
- No duplicate row appeared.

If the fetch does not show the change, wait a moment and fetch once more. If it still does not, report the row as unsaved and keep the ledger entry. Never claim a status that the page does not show.

## 6. Duplicate and already-applied handling

- Same company + role already `Applied` on this site: skip, do not add a second row.
- Same job URL already `Applied` on another site: ask the user before applying again through a second board.
- Site shows `✓ Applied` but the row is `Drafted`: do not click apply. Find the real date in the site's application history, write it to `Applied At`, and change the status to `Applied`. Say "already applied before this run" in the report.
- Site shows an application row with a different role at the same company: that is a different req. Judge per role, not per company.

## 7. Failure handling

| Situation | What to do |
|---|---|
| `old_str` matched nothing | Re-fetch, rebuild the exact row, retry once. Then report unsaved. |
| Page has a second table and no canonical row | Stop and ask which row to update. Do not guess. |
| `replace_content` would delete child content | Stop and ask. Never pass `allow_deleting_content: true` silently. |
| Notion write fails | Keep the ledger entry. Tell the user the exact error. Continue only if they say so. |
| Site submit succeeds but Notion fails | Keep the ledger entry, report the row as "applied, Notion pending", and retry once at the end. Do not resubmit the application. |
