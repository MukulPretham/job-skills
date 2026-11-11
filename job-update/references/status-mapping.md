# Status Mapping

The tracker has one status vocabulary. Do not invent a value. If the evidence does not clearly fit a row, leave the status alone and put the thread under "needs human".

## The vocabulary

| Status | Evidence required | Change? |
|---|---|---|
| `Drafted` | Harvested, never submitted. Not an application. | Never touched by this skill |
| `Applied` | Submission confirmed. Default after job-apply. | No change on a confirmation email |
| `Applied*` | Same as Applied, with a footnote from the site | Treat as Applied |
| `Pending` | The site itself shows the application as pending | Treat as Applied |
| `In Progress` | The company says it is reviewing, or the site shows under review | Change from Applied when explicit |
| `Viewed` | "Your application was viewed" or "opened your application" | Change from Applied |
| `Assessment` | Online test, coding challenge, take-home, HackerRank, Codility, TestGorilla link | Change |
| `Interview` | Interview invite, scheduling link, availability request, call request | Change |
| `Offer` | Offer letter, "pleased to offer", "we would like to offer", "selected", a start date and next steps. When the user says "accepted", this is the value: the tracker has no `Accepted` status. | Change |
| `Rejected` | Explicit rejection | Change |
| `Withdrawn` | The user withdrew and the company confirmed it | Only with the user's instruction |

A row can move forward through several stages. Use the **newest** message, not the oldest.

## Phrase table

### Rejected

Safe to change when the message is clearly about this application:

- "unfortunately, we will not be moving forward"
- "we have decided not to proceed with your application"
- "we are pursuing other candidates"
- "you have not been selected"
- "the position has been filled"
- "regret to inform you"
- "not shortlisted"

Do **not** change when:

- the word "unfortunately" appears in a newsletter or an unrelated paragraph
- the message is a job alert
- the message rejects a different role at the same company
- the message is a generic "we receive many applications" note with no decision

### Offer

Safe to change when:

- "we are pleased to offer you"
- "offer letter" attached or linked
- "we would like to offer you the position"
- "you have been selected for the role"
- "congratulations, you have been selected"
- a start date, compensation, and next steps are stated

Do **not** change when:

- "your application has been accepted for review"
- "we have accepted your application" without a role decision
- "you have been shortlisted" (that is `Interview` at most)
- a recruiter says "your profile is accepted in our database"

### Interview

Safe to change when:

- "we would like to schedule an interview"
- "interview invitation"
- "please share your availability"
- "book a time" with an interview link
- "a call with the hiring manager"
- "next round"

Do **not** change when:

- a recruiter asks a screening question before any interview
- an automated "your application is being reviewed" note
- a newsletter about interview tips

### Assessment

Safe to change when:

- "online assessment"
- "coding challenge"
- "take home assignment"
- "HackerRank", "Codility", "TestGorilla", "CodeSignal"
- a test link with a deadline

### Viewed

Safe to change when:

- "your application was viewed"
- "the employer opened your application"
- a site notification says the profile was viewed

Do **not** change on a generic profile-view notification from a recruiter who is sourcing candidates.

### In Progress

Safe to change when:

- "your application is under review"
- "we are reviewing your application"
- "the team is reviewing your profile"

Do **not** change when the row is already `Interview`, `Assessment`, or `Offer`. Never move a row backwards.

### No change

These mean the application exists, not that it progressed:

- "we received your application"
- "thank you for applying"
- "your application has been submitted"
- Indeed's automatic confirmation
- Wellfound's "application successfully submitted"
- a recruiter sourcing mail for a different role
- a job digest that mentions the company
- a LinkedIn "someone viewed your profile" alert

## Ambiguity rules

1. **Company plus role.** Match both. A company can have two rows (Rubrik, Nimble Solutions, red6.ai, and others). If only one row exists for that company, company plus the role mentioned in the email is enough.
2. **Newest wins, but never move backwards.** If the newest message is a rejection after an interview, `Rejected` is correct. If the newest is a newsletter and an older message was an interview invite, keep `Interview`.
3. **One thread, one row.** A thread about a different role is a different row.
4. **Terminal rows stay terminal unless the user asks.** Do not reopen `Offer`, `Rejected`, or `Withdrawn` on a hunch.
5. **A wrong status is worse than a stale one.** If two readings are plausible, leave the row and list it under "needs human" with the subject, sender, and date.

## Current live quirks

- **Indeed** sends an auto-confirmation for every application. It means `Applied`, nothing more.
- **Wellfound** sends digests such as "New jobs at SonicAI and 7 more". These mention companies but are not updates.
- **Shine** rows may read `Applied*` with a `~` before the time. Keep the row's local style; do not normalise the whole column.
- **Hirist** and **Shine** rows are stored as escaped paragraph text, not real table rows. Update the exact escaped fragment.
- **Hiring Cafe** applies happen on the employer ATS, so replies often come from Greenhouse, Lever, Ashby, Workable, Rippling, or SmartRecruiters rather than from the company domain.

## Report shape for needs-human

```
- <Company> / <Role>: "<subject>" from <sender>, <date>. Ambiguous because <reason>. Left at <current status>.
```
