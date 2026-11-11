# Driving the browser

How to operate the user's signed-in Chrome for any job task (Gmail lookups, Wellfound
/ Indeed / Hiring Cafe applications, status checks).

## Two tools, routed by task

Both exist on this machine and they run in **different Chrome profiles**, so they see
different signed-in sessions. Route by what the task needs:

| Task | Tool | Why |
|---|---|---|
| Read-only work: Gmail lookups, status checks, "what does this page say", browsing | `browser_exec` / `browser_cdp` over CDP on `127.0.0.1:9222` | light, no relay, no session bookkeeping |
| Submitting applications, filling forms, driving buttons inside the user's own logins | `browser-control` MCP (`mcp__browser_control__execute`) with one named session per site (`wellfound`, `indeed-apply`, `hiringcafe`) | runs the user's real `Profile 4` Chrome, which is where the job-board logins live |

When the user says to use "browser control" for applications, that is the standing
instruction, and it is correct: do **not** translate a named relay session into "one tab
of the CDP debug profile". That profile is a separate login jar and will render the site
signed out, which reads as a blocked run.

## Starting browser-control from cold

`browser-control status` printing `relay: stopped`, or `mcp__browser_control__status`
returning "relay is not reachable at http://127.0.0.1:19989", means nobody has started
the relay yet. It is not a missing feature and not a reason to switch tools.

1. The extension only connects while its Chrome window is open. Launch it:
   `open -na "Google Chrome" --args --profile-directory="Profile 4"`
2. Run one trivial execute; that starts the relay and reconnects the extension:
   `browser-control execute --file probe.js` with `probe.js` =
   `return { ok: true, url: page.url() };`
   Success shows `"connected": true` in the result's `session` block.
3. Reuse the site's existing session id (`browser-control session list`; the subcommand
   is singular). After a cold start an old session's page is `about:blank` — one
   `page.goto(url)` revives it and nothing else is lost. Snapshot refs do not survive a
   restart, so re-snapshot before every `ref()` click.

CLI facts that cost time to rediscover: `execute` has **no `--code` flag** — the code is
positional or comes from `--file`; `--session <id>` and `--json` go on every call; and
`session` takes no `--json`.

## When the run dies mid-task

`execute` returning `Target page, context or browser has been closed`, then `status`
reporting "relay is not reachable", then "extension is not connected", means the Chrome
window itself went away — not a browser-control fault, and not something another retry
fixes. Diagnose before retrying:

1. Count the app: `ps aux | grep -c "[G]oogle Chrome"`. Zero confirms it quit.
2. Relaunch (`open -a "Google Chrome"`, plus
   `--args --profile-directory="Profile 4"` when the extension must live in that
   profile) and give it ~8s.
3. `browser-control status --json` must show `extension.connected: true`.
   `activeTargets: 0` is normal here — the old page died with the window.
4. One `execute` doing `page.goto(<the URL you were on>)` re-establishes everything: the
   first operational call starts the relay, and the named session id survives the
   restart. Then **re-read the page and re-derive the answer** — evidence collected
   before the crash is not evidence about the page after it.

A `status` call reporting the relay unreachable in that window is expected and is not a
second fault: observation calls never start the relay, operational ones do. Never retry
the same `execute` unchanged more than once — check the process first.

## Start the browser

```bash
curl -s --max-time 3 http://127.0.0.1:9222/json/version   # must return JSON
```

Refused connection means the debug instance is not running. Launch it — do not report a
blocker and do not touch the user's default profile (Chrome 136+ rejects the debug flag
there):

```bash
open -na "Google Chrome" --args --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.hermes/chrome-debug" --no-first-run --no-default-browser-check
```

Poll 9222 for up to ~20s; it usually answers in 3. That profile is already signed in
(Gmail, Indeed, Wellfound). Never type a password, create an account, or solve a
CAPTCHA — hand those back to the user.

## One tab, always

Keep exactly one page target for the whole run. Extra tabs on the same site produce the
worst kind of bug: the scripted context and the rendered page diverge, so a modal looks
filled on screen and reads empty in the DOM (`textContent` 0, zero `textarea`, AX dialog
with no children).

- Audit before starting: `Target.getTargets`, then `Target.closeTarget` on every extra
  page target except the one you will drive.
- Re-check after any tool that might have opened a tab.
- A control that is visible in a screenshot but absent from `document.querySelector` is
  the signature of this collision — check tabs before suspecting a shadow root.

## Reading state

1. `page_info()` for a summary, then `js("location.href")` to confirm the bound tab is
   the page you think it is.
2. Wait for a site-specific ready signal (a results row, the job title heading, the
   apply button) — not `document.readyState`, not a fixed sleep.
3. Poll for the element you need, up to ~30s, when a dialog renders asynchronously.
4. **Return narrow shapes from `execute`.** Every result also carries the page's captured
   console buffer, and Cloudflare-fronted boards emit dozens of CSP/Turnstile entries per
   navigation, so returning whole-body text multiplies the payload without adding a fact.
   Return `{ url, title, snippet }` or the handful of parsed fields, and slice big reads
   inside the page (`document.body.innerText.slice(idx)`) instead of shipping the document.

## Typing into React inputs

Assigning `.value` directly is ignored by React. Use the native setter and dispatch the
events:

```js
const ta = document.querySelector('textarea');
const set = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
set.call(ta, text);
ta.dispatchEvent(new Event('input', {bubbles: true}));
ta.dispatchEvent(new Event('change', {bubbles: true}));
ta.focus();
```

`HTMLInputElement.prototype` for text inputs. Prefer a site's stable hook over text
matching when one exists (e.g. Wellfound's
`[data-test="JobApplicationModal--SubmitButton"]`), and read `.disabled` before
clicking — a disabled submit means a required field is still empty.

## When an element is visible but not in the DOM

Escalate in this order, and stop as soon as one works:

1. `document.querySelector` inside the page.
2. CDP `DOM.getDocument {depth: -1, pierce: true}` → `DOM.querySelectorAll` → nodeId.
3. `Accessibility.getFullAXTree` → the node's `backendDOMNodeId` → `DOM.resolveNode` →
   `Runtime.callFunctionOn` with a function that sets the value or clicks.

If all three miss while a screenshot shows the control, go back to the tab check.
`capture_screenshot()` + vision is the tiebreaker when DOM reads and the picture
disagree — trust the picture for presence, the DOM for handles.

## Verify, then log

A click is not a submission. Read back the site's own state after the fact
(`/jobs/applications`, an applied chip after a hard reload, a confirmation page) before
writing a row anywhere. Record both the applied-state check and where it was observed in
that run's notes, so a later sync can tell "applied" from "maybe".
