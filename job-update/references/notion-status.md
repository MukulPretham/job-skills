# Notion Status Updates

The tracker is flat. Every site page holds one table covering every date.

```
Job Applications                (page 40d3109c-a531-8132-847b-e945a98a70a1, 💼)
├── Wellfound                   (4113109c-a531-8184-a738-c2ff22575c43)
├── Hiring Cafe                 (4113109c-a531-819982a1d2e3afb220bb)
├── Indeed                      (4113109c-a531-8134-853b-eaf20c74551d)
├── Cutshort                    (4123109c-a531-818680e6c4559b436dc0)
├── Apna                        (4123109c-a531-817bab87cf1614cd2a02)
├── Shine                       (4123109c-a531-81acaa28dabc12cd3454)
├── Hirist                      (4123109c-a531-812286a1fdb50e79d801)
├── Run Notes                   (4113109c-a531-81a5-93b9-f1c654ae58c0)
└── Hyderabad Outreach          (4113109c-a531-810b-9468-ca04e63cc1d1)
```

Never create a date page, a second site page, or a page per application.

## 1. Fetch the page

```js
const page = await tools.notion["notion-fetch"]({ id: sitePageId });
const text = page.text;
```

Parse:

- **Real table rows**: lines starting with `| ` and ending with ` |`, after the header and separator.
- **Escaped paragraph rows**: `\| company \| role \| ... \|` joined by `<br />`. Current Shine and Hirist pages use this shape.
- **Dated second tables**: a heading like `## 11 Nov 2026 — applications sent` followed by its own table. Label these separately in the report; do not silently merge them.

For every row, capture the exact original text. Notion rewrites bare domains into links and escapes characters, so a remembered string will not match.

## 2. Match the row

Match on **company + role**, not company alone. Normalise only for comparison: lowercase, collapse whitespace, strip markdown link syntax to the URL.

If more than one row matches, list them (site, company, role, applied-at, current status) and ask which one to update. Do not guess.

If the row is in a dated second table, update it in place but say so in the report.

## 3. Replace only the Status cell

`Applied At (IST)` stays unchanged. Salary, YOE, and link stay unchanged.

### Real table row

```js
await tools.notion["notion-update-page"]({
  page_id: sitePageId,
  command: "update_content",
  content_updates: [{
    old_str: "| Acme Corp | Backend Developer | ₹6,00,000/yr | 1+ yr | Applied | 2026-11-11 15:42 IST | [Job](https://...) |",
    new_str: "| Acme Corp | Backend Developer | ₹6,00,000/yr | 1+ yr | Interview | 2026-11-11 15:42 IST | [Job](https://...) |"
  }]
});
```

### Escaped paragraph row

Replace only the escaped line fragment, keeping the `<br />` separators:

```js
old_str: "\\| Acme Corp \\| Backend Developer \\| ... \\| Applied \\| 2026-11-11 15:42 IST \\| [Job](https://...) \\|"
new_str: "\\| Acme Corp \\| Backend Developer \\| ... \\| Interview \\| 2026-11-11 15:42 IST \\| [Job](https://...) \\|"
```

### `Applied*`

Some Shine rows read `Applied*`. Replace the whole cell value with the new status (`Rejected`, `Offer`, and so on). Do not keep the asterisk on a new status.

## 4. Verify

Fetch the page again after each batch. Confirm:

- the target row shows the new status
- the `Applied At` cell is unchanged
- no other row changed
- no duplicate row appeared

If the new status is absent, wait a moment and fetch once more. If it is still absent, treat the write as failed and report it. The API response is not proof.

## 5. Failure handling

| Symptom | Action |
|---|---|
| `old_str` matched nothing | Re-fetch, rebuild from the exact row, retry once |
| More than one match | Ask which row; do not update either |
| `replace_content` would delete child pages | Stop and ask; never pass `allow_deleting_content: true` silently |
| Page fetch returns far fewer rows than usual | Re-fetch before writing; the page may be truncated |
| Notion is unreachable | Stop, keep the findings in the report, tell the user |
| Duplicate site pages already exist | Ask which one to use; do not merge or delete |

## 6. Run Notes

Append one section to `Run Notes`, newest first:

```
## YYYY-MM-DD — Gmail status sync

**Checked:** <n> rows across <n> sites
**Updated:** <n>
**Unchanged:** <n>
**Needs human:** <n>

| Site | Company | Role | Old | New | Evidence (<= 12 words) |
| --- | --- | --- | --- | --- | --- |

**Needs human:** ...
**Notes:** ...
```

Do not put application rows in Run Notes. It is a log, not a tracker.
