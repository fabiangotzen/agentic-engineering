#!/usr/bin/env python3
"""Usage: python journal.py review [journal file]"""

import re
import sys
from pathlib import Path


def open_items(text):
    items, date, in_revisit, current = [], "undated", False, None
    for line in text.splitlines():
        stripped = line.strip()
        if line.startswith("#"):
            current = None
            session = re.match(r"## (\d{4}-\d{2}-\d{2})\b", line)
            if session:
                date, in_revisit = session.group(1), False
            else:
                in_revisit = bool(re.match(r"###\s+revisit\b", line, re.I))
        elif stripped.startswith("- "):
            item = stripped[2:]
            is_open = "(recovered)" not in item and (
                in_revisit or item.startswith("❌") or item.lower().startswith("revisit:")
            )
            current = [date, item] if is_open else None
            if current:
                items.append(current)
        elif stripped and current:
            current[1] += " " + stripped
        else:
            current = None
    return sorted(items, key=lambda item: item[0])


def main(args):
    sys.stdout.reconfigure(encoding="utf-8")
    if len(args) not in (1, 2) or args[0] != "review":
        print(__doc__)
        return 2
    journal = Path(args[1] if len(args) == 2 else ".recall/journal.md")
    if not journal.is_file():
        print(f"error: journal '{journal}' does not exist. Create it as reference/journal.md describes.")
        return 2
    items = open_items(journal.read_text(encoding="utf-8"))
    print("\n".join(f"{date}  {text}" for date, text in items) or "No open weak spots. Pick a topic from recent changes instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
