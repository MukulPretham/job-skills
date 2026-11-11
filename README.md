# Job Skills

Three skills that share one Notion board, `Job Applications`, and one resume bundle.

| Skill | What it does | Writes to Notion |
|---|---|---|
| `job-find` | Asks which site and how many roles, searches the live site in the logged-in browser, screens each listing against the resume, and queues the good ones. | Adds rows with status `Drafted`. Creates the site page if it is missing. |
| `job-apply` | Reads the `Drafted` rows on one site page, re-screens each live job, applies, and verifies the submission. Waits at least 90 seconds between applications on the same site. | Flips the row from `Drafted` to `Applied` with the IST timestamp. |
| `job-update` | Reads every `Applied` or pending row, searches Gmail `mukulpretham@gmail.com` for that company and role, and classifies explicit replies. | Changes only the `Status` cell: `Interview`, `Assessment`, `Offer`, `Rejected`, and so on. |

The normal loop is:

```
/job-find wellfound 10
/job-apply wellfound 10
/job-update
```

## Layout

```
job-find/
  SKILL.md
  resume/resume.md
  resume/mukul_pretham_resume_v5.pdf
  references/candidate-profile.md
  references/site-search-playbook.md
  references/notion-board.md
  references/new-site-recon.md
  scripts/ist_now.py

job-apply/
  SKILL.md
  resume.md                     (fallback copy)
  references/answer-rules.md
  references/drafted-queue.md
  references/notion-logging.md
  references/indeed.md
  references/wellfound.md
  references/hiringcafe.md
  references/cutshort.md
  references/new-site-template.md
  references/candidate-profile.md
  references/CHANGELOG.md
  scripts/ist_now.py
  scripts/ledger.py

job-update/
  SKILL.md
  references/gmail-playbook.md
  references/status-mapping.md
  references/notion-status.md
  references/CHANGELOG.md
  scripts/ist_now.py
```

## Notion shape

`Job Applications` is flat. Each site has one page with one table. The table columns are:

```
| Company | Role | Salary | YOE Required | Status | Applied At (IST) | Link |
```

Statuses: `Drafted`, `Applied`, `Applied*`, `Pending`, `In Progress`, `Viewed`, `Assessment`, `Interview`, `Offer`, `Rejected`, `Withdrawn`.

## Browser and Notion

- Notion is reached through the `notion` MCP. It is connected to the workspace `Mukul Pretham's Notion`.
- The browser is reached through the browser MCP. On this machine it is exposed as `browse`; in other harnesses the same capability may be named `browser-control`.
- The skills never add or configure an MCP server. If the browser MCP is missing, the skill stops and tells the user to add `browser-control`.
- The skills never type a password, create an account, or solve a CAPTCHA. A login or challenge is handed to the user.

## Install

The three folders are symlinked into the OpenCode, Claude Code, Pi, Hermes, and shared-agent skill directories. The source of truth is this folder.

`_archive/` holds the pre-split `job-apply` and the legacy `job-update` for reference. Their `SKILL.md` files are renamed to `SKILL.md.archived` so a skill scanner does not load a duplicate.
