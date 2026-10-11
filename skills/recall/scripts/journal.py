#!/usr/bin/env python3
"""List the open weak spots in a recall journal, oldest first, to build a review session.

    python scripts/journal.py review <journal file>

Prints each open miss (lines that start with "- ❌") and each revisit item (lines that start with
"- revisit:" or that sit under a "### revisit" heading) with the date of its session. Leaves out lines
marked "(recovered)". Exits 0 on success and 2 on a usage or read error.

Requires Python 3 and no other packages. The journal is read, never written.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# A session heading, for example "## 2026-07-17 — topic: order pipeline".
SESSION_HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2})\b(.*)$")
# A sub-heading inside a session whose bullet items are all revisit items.
REVISIT_HEADING = re.compile(r"^###\s+revisit\b", re.IGNORECASE)
# Marker for a miss that a later session answered correctly.
RECOVERED = "(recovered)"


def open_items(text: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    date, in_revisit_section, current = "undated", False, None
    for line in text.splitlines():
        heading = SESSION_HEADING.match(line)
        if heading:
            date, in_revisit_section, current = heading.group(1), False, None
            continue
        if line.startswith("#"):
            in_revisit_section, current = bool(REVISIT_HEADING.match(line)), None
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            body = stripped[2:]
            is_open = body.startswith("❌") or body.lower().startswith("revisit:") or in_revisit_section
            current = [date, body] if is_open and RECOVERED not in body else None
            if current:
                items.append(current)
        elif stripped and current is not None:
            current[1] += " " + stripped
        else:
            current = None
    return sorted(((date, body) for date, body in items), key=lambda item: item[0])


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != "review":
        print(__doc__)
        return 2
    journal = Path(sys.argv[2])
    if not journal.is_file():
        print(f"error: journal '{journal}' does not exist. Create it as reference/journal.md describes.")
        return 2
    # Windows consoles default to a legacy code page that cannot print the journal's emoji markers.
    sys.stdout.reconfigure(encoding="utf-8")
    items = open_items(journal.read_text(encoding="utf-8"))
    if not items:
        print("No open weak spots. Pick a topic from recent changes instead.")
        return 0
    for date, body in items:
        print(f"{date}  {body}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
