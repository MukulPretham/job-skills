#!/usr/bin/env python3
"""Local job-application ledger for the job-apply skill.

Why this exists:
- Duplicate protection that survives browser session resets.
- A fallback record if a Notion write fails.
- A quick "what did I apply to recently?" view.

Storage: ~/.local/share/job-apply/ledger.jsonl (override with JOB_APPLY_LEDGER).
One JSON object per line. Stdlib only.

Usage:
    python3 ledger.py add --site Indeed --company "Acme" --role "Backend Developer" \
        --salary "₹6,00,000/yr" --yoe "1+ yr" --status Applied \
        --url "https://example.com/job/1"

    python3 ledger.py check --site Indeed --company "Acme" --role "Backend Developer"
    python3 ledger.py check --site Indeed --url "https://example.com/job/1"
    python3 ledger.py list --site Indeed --limit 20
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
DEFAULT_PATH = Path.home() / ".local" / "share" / "job-apply" / "ledger.jsonl"


def ledger_path() -> Path:
    override = os.environ.get("JOB_APPLY_LEDGER")
    return Path(override).expanduser() if override else DEFAULT_PATH


def normalize(value: str) -> str:
    """Case/punctuation-insensitive comparison key."""
    value = (value or "").casefold().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def read_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                # A corrupt line should not make the whole ledger unusable.
                continue
    return entries


def default_applied_at() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")


def cmd_add(args: argparse.Namespace) -> int:
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "site": args.site.strip(),
        "company": args.company.strip(),
        "role": args.role.strip(),
        "salary": (args.salary or "Not listed").strip(),
        "yoe_required": (args.yoe or "Not stated").strip(),
        "status": (args.status or "Applied").strip(),
        "url": (args.url or "").strip(),
        "applied_at": (args.applied_at or default_applied_at()).strip(),
        "notes": (args.notes or "").strip(),
        "recorded_at": datetime.now(IST).isoformat(timespec="seconds"),
    }

    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(json.dumps({"ok": True, "ledger": str(path), "entry": entry}, ensure_ascii=False, indent=2))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    entries = read_entries(ledger_path())
    site = normalize(args.site) if args.site else None
    company = normalize(args.company) if args.company else None
    role = normalize(args.role) if args.role else None
    url = (args.url or "").strip()

    matches: list[dict] = []
    for entry in entries:
        if site and normalize(entry.get("site", "")) != site:
            continue
        url_match = bool(url) and entry.get("url", "").strip() == url
        company_role_match = bool(company and role) and (
            normalize(entry.get("company", "")) == company
            and normalize(entry.get("role", "")) == role
        )
        if url_match or company_role_match:
            matches.append(entry)

    print(
        json.dumps(
            {
                "match": bool(matches),
                "count": len(matches),
                "matches": matches[-10:],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    entries = read_entries(ledger_path())
    site = normalize(args.site) if args.site else None
    if site:
        entries = [e for e in entries if normalize(e.get("site", "")) == site]
    limit = max(1, args.limit)
    print(json.dumps(entries[-limit:], ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local job application ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Record a verified application")
    add.add_argument("--site", required=True)
    add.add_argument("--company", required=True)
    add.add_argument("--role", required=True)
    add.add_argument("--salary", default="")
    add.add_argument("--yoe", default="")
    add.add_argument("--status", default="Applied")
    add.add_argument("--url", default="")
    add.add_argument("--applied-at", dest="applied_at", default="")
    add.add_argument("--notes", default="")
    add.set_defaults(func=cmd_add)

    check = sub.add_parser("check", help="Check for a duplicate application")
    check.add_argument("--site", default="")
    check.add_argument("--company", default="")
    check.add_argument("--role", default="")
    check.add_argument("--url", default="")
    check.set_defaults(func=cmd_check)

    lst = sub.add_parser("list", help="List recent entries")
    lst.add_argument("--site", default="")
    lst.add_argument("--limit", type=int, default=20)
    lst.set_defaults(func=cmd_list)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except BrokenPipeError:
        return 0
    except Exception as exc:  # keep the skill run alive; report the failure clearly
        print(f"ledger error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
