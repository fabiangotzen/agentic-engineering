#!/usr/bin/env python3
"""Check a package-mode overview against the rules in reference/package.md.

    python <skill folder>/scripts/check_overview.py <answer file> [--src <package folder>]

Checks the overview length, the number and format of the sequence diagrams, and the data flow line.
With --src, also checks that each participant and method name in the diagrams, and each name in
backticks in the overview, occurs in the source. Prints one line for each failure. Exits 0 when all
checks pass, 1 when a check fails, and 2 on a usage or read error.

Requires Python 3 and no other packages.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_OVERVIEW_LINES = 10
MAX_DIAGRAMS = 2
MAX_PARTICIPANTS = 6
# Lifelines that are not class names: the grouped static utilities and external systems in brackets.
NOT_A_CLASS = re.compile(r"^(helpers|\[.+\])$")
CODE_BLOCK = re.compile(r"```([^\n]*)\n(.*?)```", re.S)
CALL_ARROW = re.compile(r"-{2,}\s*([A-Za-z_]\w*)\(")
RETURN_ARROW = re.compile(r"<-( -)+")
IDENTIFIER = re.compile(r"`([A-Za-z_][\w.]*)(?:\(\))?`")
# Source files larger than this are skipped, so that a binary or generated file cannot slow the search.
MAX_SOURCE_BYTES = 2_000_000


def check_diagram(index: int, diagram: str) -> tuple[list[str], set[str]]:
    failures: list[str] = []
    lines = [line for line in diagram.splitlines() if line.strip()]
    if not lines:
        return [f"diagram {index} is empty"], set()
    participants = re.split(r"\s{2,}", lines[0].strip())
    if len(participants) > MAX_PARTICIPANTS:
        failures.append(f"diagram {index} has {len(participants)} participants (max {MAX_PARTICIPANTS})")
    calls = CALL_ARROW.findall(diagram)
    if not calls:
        failures.append(f"diagram {index} has no call arrow like ---method(args)--->")
    if not RETURN_ARROW.search(diagram):
        failures.append(f"diagram {index} has no dashed return arrow like <- - Type - -")
    names = {name for name in participants if not NOT_A_CLASS.match(name)} | set(calls)
    return failures, names


def check_text(text: str) -> tuple[list[str], set[str]]:
    failures: list[str] = []
    blocks = CODE_BLOCK.findall(text)
    if any("mermaid" in language.lower() for language, _ in blocks):
        failures.append("found a Mermaid block; use plain ASCII")
        blocks = [block for block in blocks if "mermaid" not in block[0].lower()]
    if not 1 <= len(blocks) <= MAX_DIAGRAMS:
        failures.append(f"found {len(blocks)} diagrams (need 1 to {MAX_DIAGRAMS})")
    overview = text.split("```", 1)[0]
    overview_lines = [line for line in overview.splitlines() if line.strip()]
    if len(overview_lines) > MAX_OVERVIEW_LINES:
        failures.append(f"overview has {len(overview_lines)} lines (max {MAX_OVERVIEW_LINES})")
    if not re.search(r"^Data flow:", CODE_BLOCK.sub("", text), re.M):
        failures.append("no line starts with 'Data flow:'")
    names = {part for name in IDENTIFIER.findall(overview) for part in name.split(".") if part}
    for index, (_, diagram) in enumerate(blocks, start=1):
        diagram_failures, diagram_names = check_diagram(index, diagram)
        failures += diagram_failures
        names |= diagram_names
    return failures, names


def missing_names(names: set[str], source: Path) -> list[str]:
    remaining = set(names)
    for path in source.rglob("*"):
        if not remaining:
            break
        if not path.is_file() or ".git" in path.parts or path.stat().st_size > MAX_SOURCE_BYTES:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        remaining -= {name for name in remaining if re.search(rf"\b{re.escape(name)}\b", content)}
    return sorted(remaining)


def main(argv: list[str]) -> int:
    args = argv[1:]
    source = None
    if "--src" in args:
        position = args.index("--src")
        if position + 1 >= len(args):
            print(__doc__)
            return 2
        source = Path(args[position + 1])
        del args[position : position + 2]
    if len(args) != 1:
        print(__doc__)
        return 2
    answer = Path(args[0])
    if not answer.is_file():
        print(f"error: answer file '{answer}' does not exist.")
        return 2
    if source is not None and not source.is_dir():
        print(f"error: source folder '{source}' does not exist.")
        return 2
    failures, names = check_text(answer.read_text(encoding="utf-8"))
    if source is not None:
        failures += [f"'{name}' does not occur in {source}" for name in missing_names(names, source)]
    print("\n".join(failures) if failures else "PASS: overview follows reference/package.md.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
