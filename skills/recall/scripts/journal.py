#!/usr/bin/env python3
"""List the open weak spots in a recall journal, oldest first, to build a review session.

    python <skill folder>/scripts/journal.py review [journal file]

Run it from the project root. The journal file defaults to .recall/journal.md in the current directory.
Prints each open miss (lines that start with "- ❌") and each revisit item (lines that start with
"- revisit:" or that sit under a "### revisit" heading) with the date of its session. Leaves out lines
marked "(recovered)". Exits 0 on success and 2 on a usage or read error.

Requires Python 3 and no other packages. The journal is read, never written.
"""

from __future__ import annotations

import io
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_JOURNAL = Path(".recall/journal.md")
# A session heading, for example "## 2026-07-17 — topic: order pipeline".
SESSION_HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2})\b")
# A sub-heading inside a session whose bullet items are all revisit items.
REVISIT_HEADING = re.compile(r"^###\s+revisit\b", re.IGNORECASE)
RECOVERED = "(recovered)"
MISSED = "❌"
REVISIT_PREFIX = "revisit:"


@dataclass
class Item:
    date: str
    text: str


@dataclass
class JournalParser:
    date: str = "undated"
    in_revisit_section: bool = False
    current: Item | None = None
    items: list[Item] = field(default_factory=list)

    def feed(self, line: str) -> None:
        stripped = line.strip()
        if line.startswith("#"):
            self.heading(line)
        elif stripped.startswith("- "):
            self.bullet(stripped[2:])
        elif stripped and self.current is not None:
            self.current.text += " " + stripped
        else:
            self.current = None

    def heading(self, line: str) -> None:
        self.current = None
        session = SESSION_HEADING.match(line)
        if session:
            self.date, self.in_revisit_section = session.group(1), False
        else:
            self.in_revisit_section = bool(REVISIT_HEADING.match(line))

    def bullet(self, text: str) -> None:
        self.current = Item(self.date, text) if self.is_open(text) else None
        if self.current is not None:
            self.items.append(self.current)

    def is_open(self, text: str) -> bool:
        if RECOVERED in text:
            return False
        return self.in_revisit_section or text.startswith(MISSED) or text.lower().startswith(REVISIT_PREFIX)


def open_items(text: str) -> list[Item]:
    parser = JournalParser()
    for line in text.splitlines():
        parser.feed(line)
    return sorted(parser.items, key=lambda item: item.date)


def main(argv: list[str]) -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        # Windows consoles default to a legacy code page that cannot print the journal's emoji markers.
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) not in (2, 3) or argv[1] != "review":
        print(__doc__)
        return 2
    journal = Path(argv[2]) if len(argv) == 3 else DEFAULT_JOURNAL
    if not journal.is_file():
        print(f"error: journal '{journal}' does not exist. Create it as reference/journal.md describes.")
        return 2
    items = open_items(journal.read_text(encoding="utf-8"))
    if not items:
        print("No open weak spots. Pick a topic from recent changes instead.")
    for item in items:
        print(f"{item.date}  {item.text}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
