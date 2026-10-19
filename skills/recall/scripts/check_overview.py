#!/usr/bin/env python3
"""Usage: python check_overview.py <answer file> [--src <package folder>]"""

import re
import sys
from pathlib import Path

BLOCK = re.compile(r"```([^\n]*)\n(.*?)```", re.S)
CALL = re.compile(r"-{2,}\s*([A-Za-z_]\w*)\(")
NAME = re.compile(r"`([A-Za-z_][\w.]*)(?:\(\))?`")


def check(text):
    errors, names = [], set()
    blocks = BLOCK.findall(text)
    if any("mermaid" in lang.lower() for lang, _ in blocks):
        errors.append("found a Mermaid block; use plain ASCII")
    diagrams = [body for lang, body in blocks if "mermaid" not in lang.lower()]
    if not 1 <= len(diagrams) <= 2:
        errors.append(f"found {len(diagrams)} diagrams (need 1 to 2)")
    overview = text.split("```", 1)[0]
    if len([line for line in overview.splitlines() if line.strip()]) > 10:
        errors.append("overview has more than 10 lines")
    if not re.search(r"^Data flow:", BLOCK.sub("", text), re.M):
        errors.append("no line starts with 'Data flow:'")
    for name in NAME.findall(overview):
        names.update(filter(None, name.split(".")))
    for i, diagram in enumerate(diagrams, 1):
        participants = re.split(r"\s{2,}", diagram.strip().splitlines()[0].strip()) if diagram.strip() else []
        calls = CALL.findall(diagram)
        if len(participants) > 6:
            errors.append(f"diagram {i} has {len(participants)} participants (max 6)")
        if not calls:
            errors.append(f"diagram {i} has no call arrow like ---method(args)--->")
        if not re.search(r"<-( -)+", diagram):
            errors.append(f"diagram {i} has no dashed return arrow like <- - Type - -")
        names.update(p for p in participants if p != "helpers" and not p.startswith("["))
        names.update(calls)
    return errors, names


def missing(names, src):
    text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in src.rglob("*")
        if p.is_file() and ".git" not in p.parts
    )
    return sorted(n for n in names if not re.search(rf"\b{re.escape(n)}\b", text))


def main(args):
    src = None
    if "--src" in args:
        i = args.index("--src")
        src, args = Path(args[i + 1]) if i + 1 < len(args) else None, args[:i] + args[i + 2:]
        if src is None or not src.is_dir():
            sys.exit(f"error: missing source folder\n{__doc__}")
    if len(args) != 1 or not Path(args[0]).is_file():
        sys.exit(__doc__)
    errors, names = check(Path(args[0]).read_text(encoding="utf-8"))
    if src:
        errors += [f"'{n}' does not occur in {src}" for n in missing(names, src)]
    print("\n".join(errors) or "PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
