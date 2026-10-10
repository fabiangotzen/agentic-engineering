#!/usr/bin/env python3
"""Validate every skill under skills/ against the Agent Skills rules this repository follows.

    python scripts/check_skills.py

Checks each skill's frontmatter, body size, links and scripts. Exits 0 when every check passes and 1 when
any check fails, so CI can gate on it. Requires Python 3 and no other packages.
"""

from __future__ import annotations

import py_compile
import re
import sys
import tempfile
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
# Agent Skills limits for the frontmatter fields.
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
# Token budget for the SKILL.md body, so the always-loaded part of a skill stays small.
MAX_BODY_TOKENS = 1500
# Reference files longer than this need a table of contents.
TOC_LINE_THRESHOLD = 100

failures: list[str] = []


def fail(skill: str, message: str) -> None:
    failures.append(f"{skill}: {message}")


def estimate_tokens(text: str) -> int:
    # No tokenizer dependency: take the larger of two common estimates so the budget errs on the safe side.
    return max(round(len(text) / 4), round(len(text.split()) * 1.33))


def parse_skill(path: Path) -> tuple[dict[str, str], str] | None:
    match = re.match(r"---\n(.*?)\n---\n(.*)", path.read_text(encoding="utf-8"), re.S)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            fields[key.strip()] = value.strip()
    return fields, match.group(2)


def check_skill(skill_dir: Path) -> None:
    skill = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        fail(skill, "SKILL.md is missing")
        return
    parsed = parse_skill(skill_md)
    if parsed is None:
        fail(skill, "SKILL.md has no frontmatter block")
        return
    fields, body = parsed

    name = fields.get("name", "")
    if not re.fullmatch(r"[a-z0-9-]{1,%d}" % MAX_NAME_LENGTH, name):
        fail(skill, f"name '{name}' must be 1-{MAX_NAME_LENGTH} lowercase letters, numbers or hyphens")
    if name != skill:
        fail(skill, f"name '{name}' must match the folder name '{skill}'")
    description = fields.get("description", "")
    if not description or len(description) > MAX_DESCRIPTION_LENGTH:
        fail(skill, f"description must be 1-{MAX_DESCRIPTION_LENGTH} characters (has {len(description)})")
    if "Use when" not in description:
        fail(skill, "description must contain a 'Use when …' sentence")

    tokens = estimate_tokens(body)
    if tokens > MAX_BODY_TOKENS:
        fail(skill, f"SKILL.md body is about {tokens} tokens (limit {MAX_BODY_TOKENS})")

    for markdown in skill_dir.rglob("*.md"):
        relative = markdown.relative_to(skill_dir).as_posix()
        text = markdown.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)#\s]+)\)", text):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            if relative.startswith("reference/"):
                fail(skill, f"{relative} links to {link}; reference files must not link onward")
            elif not (markdown.parent / link).is_file():
                fail(skill, f"{relative} links to {link}, which does not exist")
        if relative.startswith("reference/") and text.count("\n") > TOC_LINE_THRESHOLD and "## Contents" not in text:
            fail(skill, f"{relative} is over {TOC_LINE_THRESHOLD} lines and has no '## Contents' section")

    with tempfile.TemporaryDirectory() as scratch:
        for script in (skill_dir / "scripts").glob("*.py") if (skill_dir / "scripts").is_dir() else []:
            try:
                py_compile.compile(str(script), cfile=str(Path(scratch) / "out.pyc"), doraise=True)
            except py_compile.PyCompileError as error:
                fail(skill, f"scripts/{script.name} does not compile: {error.msg}")


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"error: {SKILLS_DIR} does not exist.")
        return 1
    skills = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
    for skill_dir in skills:
        check_skill(skill_dir)
    if failures:
        print("\n".join(f"FAIL {failure}" for failure in failures))
        return 1
    print(f"PASS: {len(skills)} skills checked ({', '.join(path.name for path in skills)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
