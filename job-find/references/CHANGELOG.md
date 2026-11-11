# Job Find — Changelog

Append a dated entry for every behavioural change. Say what changed and why.

## 2026-11-11

- **Skill created** for the split job workflow. `job-find` now owns the search and harvest step that used to live inside `job-apply`.
- **Two questions every run:** which site, and how many roles. Both use the question tool with a free-text option so the user can name a different site or quantity.
- **Resume bundle stored locally** at `resume/resume.md` and `resume/mukul_pretham_resume_v5.pdf`, so later sessions do not need to provide it again.
- **Site pages are resolved from Notion** and created as direct children of `Job Applications` when missing.
- **New rows are always `Drafted`** with `YYYY-MM-DD (drafted)`. This skill never submits an application.
- **Learning rule made explicit:** every new selector, search URL, filter, login signal, or site quirk must be written back to the site playbook before the run ends.
