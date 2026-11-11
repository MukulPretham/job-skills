# New Site Onboarding — Recon First

Use this when the user asks for a site that has no runbook in `references/` (for example LinkedIn, Naukri, Instahyre, Cutshort, Hirist). The goal is to map the site safely, write a durable runbook, and only then apply.

**Do not freestyle applications on an unknown site.** A wrong click can submit a half-filled form, apply to an out-of-scope role, or trigger an account action. Recon is cheap; a bad submission is not.

## 1. Confirm with the user

Say: "I don't have a runbook for <site> yet. I can do a recon pass first — open the site, map the search and apply flow, and write the runbook — without submitting anything. Then I'll show you the flow and start applying. OK?"

If they agree, proceed. If they want you to just start applying, explain that the skill deliberately requires a mapped flow first, and ask them to confirm the site's apply flow manually.

## 2. Recon checklist

Do this with the `browser-control` MCP, one small step at a time. Keep every diagnostic return to `{ url, title, snippet }`.

1. **Session and login**
   - Use a descriptive session name if one does not exist (for example `linkedin`).
   - Check the logged-in state from the header/avatar. If logged out, stop and ask the user to log in manually.
   - Record the exact logged-in selector and the logged-out signal.

2. **Search**
   - Find the search input and submit control.
   - Note whether URL query navigation is safe or bot-flagged.
   - Note persistent filters, saved searches, and default location.
   - Record the role keywords that produce relevant results.

3. **Listing extraction**
   - Record stable selectors for job cards: title, company, location, salary, job URL.
   - Note pagination/infinite scroll behavior.
   - Note promoted/external listings and how to spot them.

4. **Screening**
   - Open 3–5 job pages and record where years of experience, salary, and the apply control live.
   - Note external-ATS signals ("Apply on company site", "Apply by email", redirects).
   - Note duplicate/already-applied signals.

5. **Apply flow**
   - Open one job and click Apply **without submitting**. Walk to the review screen.
   - Record every step: resume selection, questions, demographics, review, submit, confirmation.
   - Note hidden inputs, label-click requirements, and React fill quirks.
   - Record the exact success signal (URL, heading, applied-state button).
   - If the site requires a resume upload or profile change, stop; do not modify the account.

6. **Required fields**
   - List every question the site asks and map it to `candidate-profile.md`.
   - Mark anything genuinely unknown as "ask the user".

7. **Pacing and failure signatures**
   - Note rate limits, CAPTCHA/Cloudflare behavior, timeout patterns, and benign console noise.

## 3. Write the runbook

Create `references/<site>.md` with this shape:

```md
# <Site> — Site Runbook

**Scope:** this run applies on <domain> only.

## 1. Golden rules
## 2. Setup and session
## 3. Quick reference: URLs and selectors
## 4. Finding candidate jobs
## 5. Screening
## 6. The apply flow
## 7. Answers to fill without asking
## 8. Verification
## 9. Rate limits, pacing, failure signatures
## 10. Reporting
## 11. Hard rules
## Field notes (append-only)
```

Include real selector snippets and a one-shot flow example, not vague advice. The next agent should be able to follow it without re-deriving the site.

## 4. Register the site

1. Add the site to the canonical-site list and the reference table in `SKILL.md`.
2. Add aliases the user might type (for example `linkedin`, `linked in`, `lnkdin`).
3. Append a dated entry to `references/CHANGELOG.md`.
4. Tell the user the recon is complete and show the mapped flow. Only then ask whether to start the first batch.

## 5. Hard rules for new sites

- Do not submit anything during recon.
- Do not create an account, type credentials, upload a resume, or change profile settings.
- Do not apply to a role with a stated minimum of 2+ years.
- Do not apply through an external ATS unless the user explicitly allows it.
- If the site's flow is unclear after a reasonable recon, stop and ask the user to walk you through it once. A human demonstration is better than guessing.
