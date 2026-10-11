#!/usr/bin/env python3
"""Validate every skill under skills/ against the Agent Skills rules this repository follows.

    python scripts/check_skills.py [skills directory]

Checks each skill's frontmatter, body size, links and scripts. Exits 0 when every check passes and 1 when
any check fails, so CI can gate on it. Requires Python 3 and no other packages.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
# Agent Skills limits for the frontmatter fields.
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
# Token budget for the SKILL.md body, so the always-loaded part of a skill stays small.
MAX_BODY_TOKENS = 1500
# Reference files longer than this need a table of contents.
TOC_LINE_THRESHOLD = 100

FRONTMATTER = re.compile(r"---\n(.*?)\n---\n(.*)", re.S)
NAME = re.compile(rf"[a-z0-9-]{{1,{MAX_NAME_LENGTH}}}")
MARKDOWN_LINK = re.compile(r"\]\(([^)#\s]+)\)")
EXTERNAL_LINK_PREFIXES = ("http://", "https://", "mailto:")


@dataclass(frozen=True)
class Skill:
    directory: Path
    fields: dict[str, str]
    body: str

    @property
    def name(self) -> str:
        return self.directory.name


def estimate_tokens(text: str) -> int:
    # No tokenizer dependency: take the larger of two common estimates so the budget errs on the safe side.
    return max(round(len(text) / 4), round(len(text.split()) * 1.33))


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    match = FRONTMATTER.match(text)
    if not match:
        return None
    header, body = match.groups()
    fields = dict(line.split(": ", 1) for line in header.splitlines() if ": " in line)
    return {key.strip(): value.strip() for key, value in fields.items()}, body


def load_skill(directory: Path) -> Skill | str:
    skill_md = directory / "SKILL.md"
    if not skill_md.is_file():
        return "SKILL.md is missing"
    parsed = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if parsed is None:
        return "SKILL.md has no frontmatter block"
    return Skill(directory, *parsed)


def check_frontmatter(skill: Skill) -> Iterator[str]:
    name = skill.fields.get("name", "")
    if not NAME.fullmatch(name):
        yield f"name '{name}' must be 1-{MAX_NAME_LENGTH} lowercase letters, numbers or hyphens"
    if name != skill.name:
        yield f"name '{name}' must match the folder name '{skill.name}'"
    description = skill.fields.get("description", "")
    if not 0 < len(description) <= MAX_DESCRIPTION_LENGTH:
        yield f"description must be 1-{MAX_DESCRIPTION_LENGTH} characters (has {len(description)})"
    if "Use when" not in description:
        yield "description must contain a 'Use when ...' sentence"


def check_body(skill: Skill) -> Iterator[str]:
    tokens = estimate_tokens(skill.body)
    if tokens > MAX_BODY_TOKENS:
        yield f"SKILL.md body is about {tokens} tokens (limit {MAX_BODY_TOKENS})"


def check_markdown_file(markdown: Path, relative: str) -> Iterator[str]:
    text = markdown.read_text(encoding="utf-8")
    is_reference = relative.startswith("reference/")
    for link in MARKDOWN_LINK.findall(text):
        if link.startswith(EXTERNAL_LINK_PREFIXES):
            continue
        if is_reference:
            yield f"{relative} links to {link}; reference files must not link onward"
        elif not (markdown.parent / link).is_file():
            yield f"{relative} links to {link}, which does not exist"
    if is_reference and text.count("\n") > TOC_LINE_THRESHOLD and "## Contents" not in text:
        yield f"{relative} is over {TOC_LINE_THRESHOLD} lines and has no '## Contents' section"


def check_markdown(skill: Skill) -> Iterator[str]:
    for markdown in sorted(skill.directory.rglob("*.md")):
        yield from check_markdown_file(markdown, markdown.relative_to(skill.directory).as_posix())


def check_scripts(skill: Skill) -> Iterator[str]:
    for script in sorted(skill.directory.glob("scripts/*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as error:
            yield f"scripts/{script.name} does not compile: {error.msg} (line {error.lineno})"


CHECKS = (check_frontmatter, check_body, check_markdown, check_scripts)


def check_skill(directory: Path) -> list[str]:
    skill = load_skill(directory)
    if isinstance(skill, str):
        return [skill]
    return [failure for check in CHECKS for failure in check(skill)]


def main(argv: list[str]) -> int:
    skills_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_SKILLS_DIR
    if not skills_dir.is_dir():
        print(f"error: {skills_dir} does not exist.")
        return 1
    skills = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    failures = [f"FAIL {skill.name}: {failure}" for skill in skills for failure in check_skill(skill)]
    if failures:
        print("\n".join(failures))
        return 1
    print(f"PASS: {len(skills)} skills checked ({', '.join(path.name for path in skills)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
