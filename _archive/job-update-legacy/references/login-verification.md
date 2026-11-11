# Login verification per site (rendered-page evidence)

Use before applying to anything from a queued batch (a dated `Draft — <date>` page, a
`Drafted` crop, or any list that spans several boards). The question to answer is
"can I submit on this board right now", site by site, before the first application.

## Protocol

1. Enumerate the **distinct sites** in the batch and count the roles per site. That
   count is what makes a signed-out board visible as lost work instead of silently
   missing roles.
2. Drive the check through the **browser-control MCP** (the user's `Profile 4`
   Chrome), not the CDP instance on `127.0.0.1:9222`. The job-board sessions live in
   `Profile 4`; a CDP tab reports them signed out and would send the user to log in to
   an account he is already in.
3. One `page.goto()` per site, then read the *rendered* state. A cookie name is a
   hint, never a verdict — `session_check.py` has no pattern for most of these boards,
   so `unknown` there means "look at the page".
4. Clicking a harmless disclosure (an avatar dropdown) is allowed and often the only
   proof. Do **not** click Apply/Submit to test login: that is an application attempt,
   not a check.
5. Report a per-site verdict with the evidence in ≤12 words, the listing count, and
   the decisions it forces (log in? authorize an ATS? which roles already fail the
   fresher gate?). A signed-out site is one decision for the user, taken before the
   batch starts, not a mid-batch surprise.

## Per-site signals

| Site | Signed in | Signed out |
|---|---|---|
| **Cutshort** | `cutshort.io/` redirects to `/profile/candidate-dashboard`; console logs `[Track] User landed on NextJS auth page {user_name: ...}`; dashboard shows applied/shortlisted counts and the user's credits | URL stays `/`, nav shows Log in / Sign up |
| **Apna** | Auth cookies `authToken`, `refreshToken`, `userId`; a real job page shows the **Apply for job** button; nav right has a round avatar + chevron that opens **View Profile / Logout** | same job page gates Apply behind login; avatar menu absent |
| **Shine** | `shine.com/` redirects to `/dashboard` showing the user's name and profile-completion %; cookies `sessionid`, `csrftoken`, `_userid_` | lands on a public home page with no name/percentage |
| **Hirist** | nav shows a profile menu rather than a Login link | nav shows `Login` / `Register` / `Login as Recruiter`; a job page logs `gladiator.hirist.tech/auth/validate` **401** and `job/magic-rank` **401**; the only cookies are analytics + Akamai (`ak_bmsc`) |
| **Stripe** | n/a — no account exists or is needed; the careers portal is public | n/a |

## Site-specific traps

- **Apna has no usable text signal.** The nav carries neither "Login" nor the user's
  name, and `apna.co/jobs/applied` 404s ("OOPS! Looks like the page you're looking for
  doesn't exist"). Use a real job page plus the avatar dropdown; text matching on the
  homepage gives a false "signed out".
- **Shine renders a stale `Register/Login` link while signed in.** The header string is
  not state-aware; the `/dashboard` redirect and the name on it are the evidence.
- **Stripe stays signed-out-looking by design.** Apply opens
  `stripe.com/careers/apply/<slug>/<gh_jid>`, which embeds
  `job-boards.greenhouse.io/embed/job_app?for=stripe&token=<gh_jid>`. A 401 from
  `my.greenhouse.io/users/self` is expected when the user has no Greenhouse account and
  does **not** block the form. Because the submit happens inside Greenhouse, Stripe is
  an **external ATS** — it needs explicit per-run authorization under `job-apply`'s
  rule 9 before submitting.
- **Hirist's `auth/validate` 401 in the console is the cleanest single signal** for any
  Hirist-family page: it fires on page load and needs no clicking. Read the console
  rather than guessing from cookies.
