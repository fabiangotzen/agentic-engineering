#!/usr/bin/env python3
"""Usage: python check_test_conventions.py <test file>..."""

import re
import sys
from pathlib import Path

TEST = re.compile(r"^\s*@(Test|ParameterizedTest)\b")
PHASE = re.compile(r"^\s*//\s*(arrange|act|assert)\b(?:\s*\+\s*(assert)\b)?", re.I)
LINE_RULES = [
    ("random-data", r"\bnew Random\(|\bRandom\(\)|UUID\.randomUUID|\bFaker\b|\.now\(\)",
     "use fixed literals or UUID.nameUUIDFromBytes"),
    ("sleep", r"Thread\.sleep", "wait with Awaitility and atMost"),
    ("junit-assert", r"\bassert(Equals|NotEquals|True|False|Null|NotNull|Same|NotSame|Throws|ArrayEquals)\(",
     "use AssertJ assertThat or assertThatThrownBy"),
    ("container-per-class", r"@Container\b|@Testcontainers\b", "start containers once per JVM in a static holder"),
    ("mock", r"@(MockBean|MockitoBean|SpyBean|MockitoSpyBean|Mock)\b|Mockito\.mock\(",
     "use a real container or WireMock, or add // allow-mock: <reason>"),
    ("spring-boot-test", r"@SpringBootTest\b", "use the project's setup meta-annotation"),
]


def method_body(lines, start):
    depth, body = 0, []
    for line in lines[start:]:
        body.append(line)
        depth += line.count("{") - line.count("}")
        if depth <= 0 and "{" in "".join(body):
            break
    return body


def check_test(lines, i):
    findings, j = [], i
    while j > 0 and lines[j - 1].strip().startswith("@"):
        j -= 1
    k = i
    while k < len(lines) and "(" not in lines[k].split("@")[0] and not re.search(r"\b(void|fun)\b", lines[k]):
        k += 1
    if not any("@DisplayName" in line for line in lines[j:k + 1]):
        findings.append((i, "display-name", 'add @DisplayName("[AREA] expected behavior")'))
    phases = []
    for line in method_body(lines, k):
        match = PHASE.match(line)
        if match:
            phases += [p.lower() for p in match.groups() if p]
    if phases != ["arrange", "act", "assert"]:
        findings.append((k, "phases", "mark // arrange, // act, // assert once each, in this order"))
    return findings


def check_file(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    tests = [i for i, line in enumerate(lines) if TEST.match(line)]
    if not tests:
        return []
    findings = [] if path.stem.endswith("IT") else [(0, "it-suffix", "end the class name with IT")]
    for i, line in enumerate(lines):
        if line.strip().startswith(("//", "*", "/*")):
            continue
        for rule, pattern, message in LINE_RULES:
            if re.search(pattern, line) and not (rule == "mock" and "allow-mock" in line):
                findings.append((i, rule, message))
    for i in tests:
        findings += check_test(lines, i)
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
