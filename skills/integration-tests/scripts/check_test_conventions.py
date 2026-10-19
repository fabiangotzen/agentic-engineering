#!/usr/bin/env python3
"""Usage: python check_test_conventions.py <test file>..."""

import re
import sys
from pathlib import Path

TEST = re.compile(r"^\s*@(Test|ParameterizedTest)\b")
SEED = re.compile(r"@Seed\((\d+)L?\)")
PHASE = re.compile(r"^\s*//\s*(arrange|act|assert)\b(?:\s*\+\s*(assert)\b)?", re.I)
IMAGE = re.compile(r'"[a-z0-9./-]+:(latest|\d+(\.\d+)?(-[\w.]+)?)"')
LINE_RULES = [
    ("random-data", r"\bnew Random\(|\bRandom\(\)|UUID\.randomUUID|\bFaker\b",
     "use fixed literals, UUID.nameUUIDFromBytes or Instancio with a seed"),
    ("time", r"\.now\((?![^)]*[cC]lock)", "read time from the injected Clock"),
    ("sleep", r"Thread\.sleep", "wait with Awaitility and atMost"),
    ("junit-assert", r"\bassert(Equals|NotEquals|True|False|Null|NotNull|Same|NotSame|Throws|ArrayEquals)\(",
     "use AssertJ assertThat or assertThatThrownBy"),
    ("container-per-class", r"@Container\b|@Testcontainers\b", "start containers once per JVM in a static holder"),
    ("mock", r"@(MockBean|MockitoBean|SpyBean|MockitoSpyBean|Mock)\b|Mockito\.mock\(",
     "use a real container or WireMock, or add // allow-mock: <reason>"),
    ("spring-boot-test", r"@SpringBootTest\b", "use the project's setup meta-annotation"),
    ("size", r"\.hasSize\w*\(|\.(size|count)\(\)\)\.is",
     "assert on content, for example extracting(Order::getId).containsExactlyInAnyOrder(...)"),
    ("order", r"\.containsExactly(ElementsOf)?\(",
     "assert in any order, or query with ORDER BY and add // allow-order: <reason>"),
]


def method_body(lines, start):
    depth, end = 0, start
    for end in range(start, len(lines)):
        depth += lines[end].count("{") - lines[end].count("}")
        if depth <= 0 and "{" in "".join(lines[start:end + 1]):
            break
    return range(start, end + 1)


def check_test(lines, i, seeds, kotlin):
    findings, j, k = [], i, i
    while j > 0 and lines[j - 1].strip().startswith("@"):
        j -= 1
    while k < len(lines) and "(" not in lines[k].split("@")[0] and not re.search(r"\b(void|fun)\b", lines[k]):
        k += 1
    annotations, body = "\n".join(lines[j:k + 1]), method_body(lines, k)
    if "@DisplayName" not in annotations:
        findings.append((i, "display-name", 'add @DisplayName("[AREA] expected behavior")'))
    if seeds is not None and not any(".withSeed(" in lines[n] for n in body):
        seed = SEED.search(annotations)
        if not seed:
            findings.append((i, "instancio-seed", "add a per-test @Seed(<number>) for Instancio data"))
        elif seed.group(1) in seeds:
            findings.append((i, "instancio-seed", f"seed {seed.group(1)} is used by another test; use a unique seed"))
        else:
            seeds.add(seed.group(1))
    phases = [(n, p.lower()) for n in body if (m := PHASE.match(lines[n])) for p in m.groups() if p]
    if [p for _, p in phases] != ["arrange", "act", "assert"]:
        findings.append((k, "phases", "mark // arrange, // act, // assert once each, in this order"))
    else:
        act = [lines[n].strip() for n in range(phases[1][0] + 1, phases[2][0]) if lines[n].strip()]
        actions = len([a for a in act if not a.startswith((".", ")"))]) if kotlin else sum(a.count(";") for a in act)
        if actions > 1:
            findings.append((phases[1][0], "one-action", "keep exactly one action under // act"))
    return findings


def check_file(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    code = [(i, line) for i, line in enumerate(lines) if not line.strip().startswith(("//", "*", "/*"))]
    findings = [(i, "image-tag", "pin the full image version, for example postgres:16.4-alpine")
                for i, line in code if IMAGE.search(line)]
    tests = [i for i, line in enumerate(lines) if TEST.match(line)]
    if tests:
        if not path.stem.endswith("IT"):
            findings.append((0, "it-suffix", "end the class name with IT"))
        for i, line in code:
            for rule, pattern, message in LINE_RULES:
                if re.search(pattern, line) and f"allow-{rule}" not in line:
                    findings.append((i, rule, message))
        text = "\n".join(lines)
        if "@Seed(" in text and "InstancioExtension" not in text:
            findings.append((0, "instancio-extension", "add @ExtendWith(InstancioExtension.class), or @Seed has no effect"))
        seeds = set() if "Instancio." in text else None
        for i in tests:
            findings += check_test(lines, i, seeds, path.suffix == ".kt")
    return [f"{path}:{i + 1}: [{rule}] {message}" for i, rule, message in sorted(findings)]


def main(args):
    files = [Path(a) for a in args if a.endswith((".java", ".kt"))]
    if not files or any(not f.is_file() for f in files):
        print(__doc__)
        return 2
    findings = [f for path in files for f in check_file(path)]
    print("\n".join(findings) or f"PASS: {len(files)} files checked")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
