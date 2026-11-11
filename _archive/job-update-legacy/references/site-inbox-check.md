# Reading a board's own inbox / status page

Answer "am I getting any messages / any replies on <board>" from the **board's own
conversations page**, driven through the `browser-control` MCP. Gmail is the wrong
source for this question: board messages are frequently not mirrored to email, and a
board with zero conversations still generates plenty of application mail. Gmail can
say "no mail" while the board says 13 pending applications.

This is the read-only sibling of `login-verification.md`: that file proves *can I
submit*, this one proves *did anyone answer*.

## Protocol

1. One named browser-control session per board (`cutshort`, `wellfound`,
   `indeed-apply`, `hiringcafe`). Never the CDP debug instance on `127.0.0.1:9222` —
   different profile, so the board renders signed out.
2. Confirm the identity from the page before reading counts: the dashboard greeting /
   profile name, or the board's own console line
   (`[Track] User landed on NextJS auth page {user_name: ...}` on NextJS boards). A URL
   that stays on the public home page means the session is dead — report that, never
   "no messages".
3. Read **both** the aggregate counters and the conversation list. The counters are
   what distinguish "no messages" from "nothing loaded": empty list + non-zero
   application counters is a healthy read of zero messages; empty list + blank counters
   is a failed render — retry once, then report unverified.
4. Report the board's own numbers verbatim and say which were counted, so the user can
   see the difference between *messages* and *application stage*.

## Cutshort

- Inbox / conversations: `https://cutshort.io/profile/candidate-conversations?i=all`
- Stage filters on that same URL: `stage=unread` (new replies), `stage=awaiting`
  (applications with no employer decision), `stage=nottakenforward` (closed/rejected).
  Omitting `stage` shows everything.
- Dashboard: `https://cutshort.io/profile/candidate-dashboard` (where `cutshort.io/`
  lands when signed in).
- `/messages` and `/dashboard` are **404** — every real path lives under `/profile/...`.
  Do not probe guessed paths twice; go to `/` and read the nav links instead.
- Counters to quote: dashboard `Conversations with companies N`,
  `Companies interested in you N`, `Applications pending / shortlisted / rejected N`;
  conversations page `Employer actions on your N applications` plus the
  `Pending | Shortlisted | Closed` tab counts.
- **The tab strip counts are authoritative; the list is virtualized.** A header of 13
  renders ~8 rows. Report the header count and state how many rows actually rendered
  rather than implying the list is complete.
- **Tab labels are not clickable locators.** `getByText('Pending', { exact: true })`
  times out; navigate with the `stage=` query param instead.
- A row reads: company, `For job <role>`, a relative time, and a chip such as
  `[Questionnaire]`. The chip is the employer's action on the application — not a
  message, and not a reply.
- Cloudflare Turnstile noise floods the console on every load (CSP
  "Connecting to 'data:,'", "No available adapters."). It is not a block.
- Zero platform messages is normal for a fresher account: Cutshort recruiters contact
  through the application list, so "no conversations" plus "N pending" is the honest
  answer, not a failure to read.

## Opening one thread

- Conversation rows are `<div>`s with JS click handlers: `a[href*="thread="]` returns
  zero nodes, so there is nothing to harvest. Click a row, then read `location.href` —
  the detail view appends `&thread=<id>` to the same conversations URL. Collect the ids
  once that way, then drive
  `...candidate-conversations?i=all&stage=awaiting&thread=<id>` directly; it is faster
  and re-entrant than re-finding rows in the list.
- Match the row to open with `innerText.includes('<Company>') && innerText.includes('For job')`
  and a length bound (`< 400`). Without the length bound the match climbs to the page
  wrapper and clicks the whole list.
- The thread panel begins after the row list: slice `document.body.innerText` from
  `View full job description` and you get your intro message, the recruiter reply, the
  questionnaire and the composer. Walking up from that anchor to the page root instead
  returns the whole page and truncates before the conversation.

## Acting on a pending questionnaire

Verified on Cutshort's NextJS thread view; check for the same structure before assuming
it elsewhere.

- Read the answered/not marker first: the panel ends in `Questionnaire submitted!` when
done, and shows a live `Submit` button with unselected options when not. Do this before
any planning — several threads are usually already answered.
- Each question is a `<fieldset>` with the question in its `<legend>`; there is **no
  `<input type="radio">` anywhere**. Options are `div[tabindex="0"]`: label text in a
  child div, radio indicator as the first child div.
- **Selected state lives on the indicator child, not the label.** Selected =
  indicator class containing `eMTsng` (with a nested dot); unselected = `cPLusq`. The
  label div's own class never changes, so a before/after `className` compare on the text
  element reports a false "did not register".
- Click the label text: `page.getByText(label, { exact: true }).first().click()`.
- Submit with the `button[type="submit"]` inside that `<form>` (it reads `Submit`).
- A confirm modal follows: "Responses cannot be changed after submission. Are you
  sure?" — read it, then click exact-text `Yes` (`getByText('Yes', { exact: true })`;
  the option labels are `Yes, this works`, so exact matching stays unambiguous).
- **Verification is two signals**: `Questionnaire submitted!` in the thread text *and* a
  console event `[Track] Submitted screening answers successfully {jobid: ...}`. A
  cleared form or a returning click proves nothing.
- Re-open every thread afterwards and report what is still open; submit in one thread per
  navigate so a failure does not leave a half-answered form behind.
- The `cf-turnstile-response` hidden input stays empty and does not block submission —
  do not chase it.
- Option phrasing per question: onsite role → `I am not in this location but can
  relocate`; **remote** role → `I am currently in this location and okay with it` (the
  same three choices are offered for a remote posting, and "can relocate" is nonsense
  there); notice → `Served notice, available immediately`.

## Replying in the thread

Sending a message is a second, separate step after answering a questionnaire, and it is
often the part that actually moves the application: the questionnaire is a form, a short
message with a human on the other end is what gets a call scheduled.

- Composer is `textarea[placeholder="Type your message..."]`; send with the button named
  exactly `Send`. `ta.fill(msg)` then
  `getByRole('button', { name: 'Send', exact: true })` works with no React-setter
  workaround.
- Verify by **reloading the thread** and finding the message text with a fresh relative
  timestamp (`a few seconds ago`). The thread also fires a console event
  `[Track] Clicked to send message on conversation page`. An optimistic DOM append proves
  nothing on its own.
- Voice, every time: greet the recruiter by first name, two or three sentences, plain
  cold text, no em dashes and no `--`, no bullets. Name the concrete ask (answers
  submitted, can join immediately, open to a call or technical round) and stop.
- Prefer a thread whose footer shows a recently active recruiter
  (`The recruiter was last active on this job 5 days ago`); a live recruiter plus a
  submitted questionnaire is the best use of one message.

## Other boards

Add a section here when a board's own inbox is mapped for the first time (Wellfound
messages, Indeed My Jobs, Hiring Cafe inbox). Keep it to URLs, counters, and the read
traps — the apply flows stay in `job-apply`'s per-site references.
