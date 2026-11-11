#!/usr/bin/env python3
"""
session_check.py — cheap per-site "am I logged in?" probe for the live Chrome.

Usage:
    python3 session_check.py wellfound
    python3 session_check.py indeed gmail hiringcafe

Output: JSON array, one object per site:
    {"site","domain","logged_in":bool,"auth_cookies":[...],"n_cookies":int}

Method: reads cookies over CDP (no page navigation, no tab, ~200ms).
Exit 0 always unless CDP is unreachable (exit 2).

Auth heuristics are per-site: a site counts as logged in only when a cookie that
represents an authenticated session for that domain is present. Marketing /
analytics cookies (GA, __cf_*, OptanonConsent) are ignored.
"""
import json
import sys

import websocket  # websocket-client

CDP_HOST = "http://127.0.0.1:9222"

# site -> dict:
#   domain  : cookie-domain suffix
#   pattern : regex over cookie names that implies an authenticated session
#   verified: date this pattern was last CONFIRMED against a real logged-in
#             session on this machine, or None if it is an educated guess.
#             An unverified pattern can never return "signed-out" — only "unknown".
SITES = {
    "wellfound": {
        "domain": "wellfound.com",
        "pattern": r"(?i)^(_wellfound$|talent_session)",
        "verified": "2026-11-06",
        "note": "confirmed against a live signed-in session; auth carrier is the httpOnly _wellfound cookie (rl_session/rl_user_id are Reforge analytics, not auth)",
    },
    "indeed": {
        "domain": "indeed.com",
        "pattern": r"(?i)(PassportAuthProxy|PPID|rememberMe|JSESSIONID)",
        "verified": "2026-11-06",
        "note": "confirmed against a live authenticated session",
    },
    "hiringcafe": {
        "domain": "hiring.cafe",
        "pattern": r"(?i)(session|token|auth|sb-)",
        "verified": None,
        "note": "GUESS - 0 cookies ever observed; site never signed in on this profile",
    },
    "gmail": {
        "domain": "google.com",
        "pattern": r"(?i)^(SID|__Secure-1PSID|__Secure-3PSID)$",
        "verified": "2026-11-06",
        "note": "CANARY - known signed in; if this reads false the PATTERNS are stale, not the session",
    },
    "linkedin": {
        "domain": "linkedin.com",
        "pattern": r"(?i)(li_at|JSESSIONID)",
        "verified": None,
        "note": "GUESS - 7 cookies, none auth; not signed in here",
    },
}


def _get(path):
    import urllib.request
    with urllib.request.urlopen(CDP_HOST + path, timeout=15) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def any_page_ws():
    for t in _get("/json/list"):
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            return t["webSocketDebuggerUrl"]
    raise RuntimeError("no page target available")


def all_cookies(ws_url):
    ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
    try:
        ws.send(json.dumps({"id": 1, "method": "Storage.getCookies", "params": {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg["result"].get("cookies", [])
    finally:
        try:
            ws.close()
        except Exception:
            pass


def check(site, cookies):
    import re
    key = site.lower()
    if key not in SITES:
        return {"site": site, "error": "unknown site; add it to SITES", "logged_in": None, "verdict": "unknown"}
    spec = SITES[key]
    domain, auth_rx = spec["domain"], spec["pattern"]
    rx = re.compile(auth_rx)
    mine = [c for c in cookies if c.get("domain", "").lstrip(".").endswith(domain)]
    auth = sorted({c["name"] for c in mine if rx.search(c["name"])})
    if auth:
        verdict = "logged-in"
    elif spec["verified"] is None:
        # An unverified pattern proves nothing when it does not match: the cookie
        # may simply be called something else. Never report this as signed-out.
        verdict = "unknown"
    else:
        verdict = "signed-out"
    return {
        "site": site,
        "domain": domain,
        "logged_in": bool(auth),
        "verdict": verdict,
        "pattern_verified": spec["verified"],
        "note": spec["note"],
        "auth_cookies": auth,
        "n_cookies": len(mine),
    }


if __name__ == "__main__":
    sites = sys.argv[1:] or list(SITES)
    try:
        cookies = all_cookies(any_page_ws())
    except Exception as e:
        print(json.dumps({"error": "CDP unreachable on %s: %s" % (CDP_HOST, e)}))
        sys.exit(2)
    print(json.dumps([check(s, cookies) for s in sites], indent=1))
