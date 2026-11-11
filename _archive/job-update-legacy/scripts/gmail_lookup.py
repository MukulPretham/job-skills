#!/usr/bin/env python3
"""
gmail_lookup.py — read Gmail search results from the live Chrome debug session.

Usage:
    python3 gmail_lookup.py "Quantanite"
    python3 gmail_lookup.py "Skoot" --json

Requires:
  - Chrome running with --remote-debugging-port=9222
    (verified live: --user-data-dir=$HOME/.hermes/chrome-debug, signed in as the user)
  - python3 with `websocket-client` (installed on /usr/bin/python3 here)

Output (default): human-readable JSON on stdout:
    {"query": ..., "count": "1–2 of 2", "threads": [{"sender":..., "subject":...,
     "snippet":..., "date":...}, ...], "raw": "<trimmed text>"}

Exit codes: 0 ok, 2 CDP unreachable, 3 search page never loaded.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

import websocket  # websocket-client

CDP_HOST = "http://127.0.0.1:9222"


def _http(path, method="GET"):
    req = urllib.request.Request(CDP_HOST + path, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def new_tab(url):
    # Newer Chrome requires PUT for /json/new
    web = urllib.parse.quote(url, safe="")
    try:
        return _http("/json/new?" + web, method="PUT")
    except Exception:
        return _http("/json/new?" + web, method="GET")


def close_tab(tid):
    try:
        urllib.request.urlopen(CDP_HOST + "/json/close/" + tid, timeout=10).read()
    except Exception:
        pass


class Page:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=60, suppress_origin=True)
        self.n = 0

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def eval(self, expr):
        r = self.call(
            "Runtime.evaluate",
            expression=expr,
            returnByValue=True,
            awaitPromise=True,
        )
        return r.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


EXTRACT_JS = r"""
(() => {
  const txt = document.body ? document.body.innerText : "";
  // textContent works even in a background tab, where innerText comes back empty.
  const T = e => { if (!e) return ""; const t = e.innerText; if (t && t.trim()) return t.replace(/\s+/g," ").trim(); return (e.textContent || "").replace(/\s+/g," ").trim(); };
  const rows = [];
  document.querySelectorAll("tr.zA").forEach(tr => {
    const g = sel => T(tr.querySelector(sel));
    rows.push({
      sender: g(".yX.xY") || g(".yW span") || g("span[email]"),
      subject: g(".y6 span") || g(".y6"),
      snippet: g(".y2"),
      date: g(".xW span") || g("span[title]")
    });
  });
  let raw = T(document.body);
  const t = document.querySelector("table.F.cf.zt");
  if (t) raw = T(t);
  return {rows: rows, raw: raw, title: document.title, href: location.href};
})()
"""


def lookup(query, wait_s=25):
    url = "https://mail.google.com/mail/u/0/#search/" + urllib.parse.quote(query, safe="")
    tab = new_tab(url)
    tid = tab.get("id")
    ws_url = tab.get("webSocketDebuggerUrl")
    if not ws_url:
        raise SystemExit(json.dumps({"error": "no webSocketDebuggerUrl from /json/new"}))
    page = Page(ws_url)
    try:
        page.call("Runtime.enable")
        deadline = time.time() + wait_s
        data = None
        done = False
        while time.time() < deadline:
            data = page.eval(EXTRACT_JS)
            body = (data or {}).get("raw") or ""
            rows = (data or {}).get("rows") or []
            if rows:
                done = True
                break
            if "No conversations" in body or re.search(r"\d+\s*[–-]\s*\d+\s+of\s+\d+", body):
                done = True
                # let rows render if the header already appeared
                time.sleep(1.0)
                data = page.eval(EXTRACT_JS)
                break
            time.sleep(1.0)
        if not data:
            print(json.dumps({"query": query, "error": "no data from page"}))
            sys.exit(3)

        rows = data.get("rows") or []
        raw = (data.get("raw") or "").strip()
        # count line like "1–2 of 2"
        count = ""
        for line in raw.splitlines()[:60]:
            s = line.strip()
            if re.match(r"^\d+\s*[–-]\s*\d+\s+of\s+\d+$", s) or "No conversations" in s:
                count = s
                break
        return {
            "query": query,
            "count": count,
            "n_rows": len(rows),
            "threads": rows[:40],
            "raw": raw[:6000],
        }
    finally:
        page.close()
        if tid:
            close_tab(tid)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: gmail_lookup.py <query>", file=sys.stderr)
        sys.exit(1)
    try:
        _http("/json/version")
    except Exception as e:
        print(json.dumps({"error": "CDP unreachable on %s: %s" % (CDP_HOST, e)}))
        sys.exit(2)
    print(json.dumps(lookup(sys.argv[1]), indent=1, ensure_ascii=False))
