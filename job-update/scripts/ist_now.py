#!/usr/bin/env python3
"""Print the current date and time in IST (Asia/Kolkata).

Used by the job-apply skill so the Applied At cells are
always in the user's timezone, regardless of the machine's local timezone.

Usage:
    python3 ist_now.py
    python3 ist_now.py --json
    python3 ist_now.py --date-only
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def main() -> None:
    parser = argparse.ArgumentParser(description="Current date/time in IST")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    parser.add_argument(
        "--date-only", action="store_true", help="Print only the YYYY-MM-DD date"
    )
    args = parser.parse_args()

    now = datetime.now(IST)

    if args.date_only:
        print(now.strftime("%Y-%m-%d"))
        return

    if args.json:
        print(
            json.dumps(
                {
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M"),
                    "timezone": "IST",
                    "iso": now.isoformat(timespec="seconds"),
                    "applied_at": now.strftime("%Y-%m-%d %H:%M IST"),
                },
                ensure_ascii=False,
            )
        )
        return

    print(now.strftime("%Y-%m-%d"))
    print(now.strftime("%Y-%m-%d %H:%M IST"))


if __name__ == "__main__":
    main()
