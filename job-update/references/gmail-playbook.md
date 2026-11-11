# Gmail Playbook

Gmail is read through the user's signed-in browser. No OAuth setup, no API key, no credential entry.

## 1. Open and verify the account

```js
await page.goto('https://mail.google.com/mail/u/0/#inbox', {
  waitUntil: 'domcontentloaded',
  timeout: 60000
});
await page.waitForTimeout(4000);

const state = await page.evaluate(() => {
  const account = document.querySelector('a[aria-label*="Google Account"]');
  return {
    url: location.href,
    title: document.title,
    account: account ? account.getAttribute('aria-label') : '',
    hasSignIn: /Sign in/i.test(document.body.innerText || ''),
    body: (document.body.innerText || '').slice(0, 300)
  };
});
return state;
```

Healthy state:

- `url` contains `mail.google.com`
- `account` contains `mukulpretham@gmail.com`
- `title` contains `Inbox`
- `hasSignIn` is false

If the URL goes to `accounts.google.com`, or the page shows `Sign in`, stop and hand off to the user. Never type a password, solve a CAPTCHA, or pick a Google account yourself.

If the account chip shows a different address, ask the user to switch to `mukulpretham@gmail.com`. Do not search another mailbox.

## 2. Search

Build the URL directly. The search query is URL-encoded after `#search/`:

```js
const q = '"Acme Corp" newer_than:60d';
await page.goto(
  'https://mail.google.com/mail/u/0/#search/' + encodeURIComponent(q),
  { waitUntil: 'domcontentloaded', timeout: 60000 }
);
await page.waitForTimeout(3000);
```

Wait until one of these is true:

- at least one `tr.zA` row exists
- the page contains `No messages matched your search`

Do not treat the sidebar label `Conversations` as a ready signal. It renders before results and produces false negatives.

Useful queries:

| Goal | Query |
|---|---|
| Company mail | `"<Company>" newer_than:60d` |
| Company plus role | `"<Company>" ("<Role>" OR application) newer_than:60d` |
| ATS confirmations | `from:(greenhouse OR lever OR workable OR ashbyhq OR smartrecruiters OR rippling OR workday OR icims OR successfactors) newer_than:60d` |
| Rejections | `("<Company>") (unfortunately OR rejected OR "not moving forward" OR "other candidates") newer_than:60d` |
| Interviews | `("<Company>") (interview OR schedule OR availability) newer_than:60d` |

Create one query per company. Keep a list of companies already resolved by the broad sweep, and skip their per-company pass.

## 3. Extract result rows

```js
const rows = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('tr.zA')).slice(0, 40).map((row, i) => {
    const sender = row.querySelector('span[email]');
    const subject = row.querySelector('.y6 span, .bog');
    const snippet = row.querySelector('.y2');
    const date = row.querySelector('.xW span, .y5');
    return {
      i,
      sender: sender ? (sender.getAttribute('email') || sender.innerText) : '',
      subject: subject ? subject.innerText.trim() : '',
      snippet: snippet ? snippet.innerText.trim() : '',
      date: date ? date.getAttribute('title') || date.innerText.trim() : '',
      unread: row.classList.contains('zE')
    };
  });
});
return rows;
```

Notes:

- `tr.zA` is the result row. An empty list means either no results or a page that did not load; check for `No messages matched your search` before concluding "no mail".
- Snippets are truncated around 150 characters. If the meaning hinges on the hidden part, open the thread.
- The sender domain matters. ATS confirmations come from `greenhouse`, `lever`, `workable`, `ashbyhq`, `smartrecruiters`, `rippling`, or `myworkdayjobs`, not always from the employer.
- A digest can mention many companies in one snippet. Do not treat a digest mention as an application update.

## 4. Open a thread

Click the row or its subject link, wait for the thread to render, then read the bodies:

```js
const thread = await page.evaluate(() => {
  const bodies = Array.from(document.querySelectorAll('div.a3s'))
    .map(el => (el.innerText || '').trim())
    .filter(Boolean);
  return {
    url: location.href,
    subject: (document.querySelector('h2.hP')?.innerText || '').trim(),
    bodies: bodies.slice(-4)
  };
});
return thread;
```

Read the newest message first. Older quoted text is below and may contain the earlier stages. Use the newest explicit statement for the status.

Return to the result list with the browser back button, or re-run the same search URL. Do not leave many Gmail tabs open.

## 5. Status signals

The full mapping is in `status-mapping.md`. Search for these phrases when reading:

**Positive progression**

- `viewed your application`, `opened your application`
- `online assessment`, `coding challenge`, `take home`, `HackerRank`, `Codility`, `TestGorilla`
- `schedule an interview`, `interview invitation`, `availability`, `book a time`, `call with`
- `offer letter`, `pleased to offer`, `we would like to offer`, `selected`, `congratulations`

**Negative**

- `unfortunately`
- `not moving forward`
- `other candidates`
- `decided not to proceed`
- `regret to inform`
- `position has been filled`
- `not selected`

**Neutral**

- `we received your application`
- `application submitted`
- `under review`
- `reviewing your application`
- `thank you for applying`

Neutral mail does not promote a row past `Applied` or `In Progress`.

## 6. Failure signatures

| Symptom | Meaning | Action |
|---|---|---|
| `raw` body empty | Tab never loaded | Retry once, then mark the row `unverified`, never "no mail" |
| `n_rows` 0 and no "No messages matched" | Failed lookup | Wait 2 seconds, retry once |
| URL becomes `accounts.google.com` | Signed out | Hand off to the user |
| "Verify it's you" / CAPTCHA | Google challenge | Hand off; do not retry-loop |
| Search page renders but rows are stale | Previous query still in the DOM | Wait for the result count to change, or reload once |
| A company search returns hundreds of digest rows | Generic name | Add the role or `application`, or search the ATS sender |
| Thread body hidden behind "Show trimmed content" | Quoted text collapsed | Read the visible newest message; only expand if the newest is unclear |

## 7. Read-only rules

- Never send, reply, forward, archive, delete, label, or report mail.
- Never click a link inside an email, especially an assessment or interview link. Reading the text is enough.
- Never download attachments.
- Never type credentials or one-time codes.
- Opening a thread marks it read. That is acceptable. Do not mark anything unread, starred, or important.

## 8. Pacing

- 2 to 3 seconds between searches.
- One search at a time. Do not parallelise Gmail in one session.
- If the user wants several sites updated, still use one Gmail tab and one search loop.

## Field notes (append-only)

- 2026-11-11 — Playbook created for the split `job-update` skill. Selectors are the standard Gmail result-row shape (`tr.zA`, `span[email]`, `.y6`, `.y2`); validate against the live page on the first run and append any drift here.
