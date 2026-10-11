#!/usr/bin/env python3
"""Lookout: spot where change and complexity meet, hold the line with ratchets, and score the risk of a change.

    python lookout.py survey [--days 90] [--top 15] [--json]
    python lookout.py ratchet init|check|tighten [--baseline .lookout/ratchets.json]
    python lookout.py risk [--base origin/main] [--markdown]

Requires git, Python 3 and the lizard package: pip install lizard
Language support is whatever lizard reads: Java, Kotlin, C/C++, C#, Go, Python, JavaScript/TypeScript, Rust,
Swift and more.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import math
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import lizard
    from lizard_languages import get_reader_for
except ImportError:
    sys.exit("lookout needs lizard: pip install lizard")

# Cyclomatic complexity above which a function counts as a warning.
CCN_WARN = 15
# Cyclomatic complexity above which a function is critical; ratchets track every file over it.
CCN_CRIT = 25
# Complexity floor for "complexity added": increases below it are noise from small new functions.
CCN_NOTABLE = 10
# Function length in lines above which a function counts as long.
LONG_FUNCTION = 100
# Paths skipped by default: dependencies, build output and generated or binary assets.
DEFAULT_EXCLUDES = ["*/node_modules/*", "*/vendor/*", "*/build/*", "*/dist/*", "*/generated/*", "*/assets/*"]
# A path segment containing one of these marks a test file.
TEST_MARKERS = ("test", "spec")
# Normalised hotspot score from which a file over CCN_WARN counts as a hotspot file.
HOTSPOT_FILE_THRESHOLD = 0.25
# Risk score from which a sounding is high, and from which it is medium.
RISK_HIGH = 60
RISK_MEDIUM = 30
# Complexity added at which the complexity factor reaches 1.
COMPLEXITY_SATURATION = 30
# Orders of magnitude of changed lines at which the size factor reaches 1 (3 means 1,000 lines).
SIZE_LOG_DECADES = 3
# Extra top-level areas at which the spread factor reaches 1.
SPREAD_SATURATION = 4
# Number of files listed under "review these first".
REVIEW_FIRST_LIMIT = 8
# Factor weights; they sum to 1. Read reference/risk-model.md before changing them.
WEIGHTS = {
    "change size": 0.20,
    "hotspot exposure": 0.30,
    "complexity added": 0.25,
    "missing test changes": 0.15,
    "spread across top-level areas": 0.10,
}
# Default churn window in days and default number of hotspots that survey prints.
DEFAULT_DAYS = 90
DEFAULT_TOP = 15


def git(*args: str, check: bool = False) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout if result.returncode == 0 else ""


def repo_root() -> Path:
    root = git("rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("error: not inside a git repository. Run lookout from a git working tree.")
    return Path(root)


def merge_base_of(base: str) -> str:
    merge_base = git("merge-base", base, "HEAD").strip()
    if not merge_base:
        sys.exit(f"error: no merge base between '{base}' and HEAD. Fetch the base branch or pass --base <branch>.")
    return merge_base


def load_baseline(path: Path) -> dict:
    try:
        baseline = json.loads(path.read_text())
        baseline["totals"], baseline["worst_ccn_by_file"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        sys.exit(f"error: cannot read the baseline {path}: {error}. Fix the file or run 'ratchet init'.")
    return baseline


def is_excluded(path: str, excludes: list[str]) -> bool:
    return any(fnmatch.fnmatch("/" + path, pattern) for pattern in excludes)


def is_test(path: str) -> bool:
    lowered = path.lower()
    return any(marker in part for part in lowered.split("/") for marker in TEST_MARKERS)


def analyzable(path: str, excludes: list[str]) -> bool:
    return get_reader_for(path) is not None and not is_excluded(path, excludes)


@dataclass
class FileMetrics:
    path: str
    nloc: int = 0
    worst_ccn: int = 0
    functions_over_warn: int = 0
    functions_over_crit: int = 0
    long_functions: int = 0
    churn: int = 0
    hotspot: float = 0.0
    test: bool = False
    functions: dict[str, int] = field(default_factory=dict)


def measure(path: str, source: str) -> FileMetrics:
    metrics = FileMetrics(path=path, test=is_test(path))
    try:
        info = lizard.analyze_file.analyze_source_code(path, source)
    except Exception as error:  # lizard can fail on unusual syntax; one file must not stop the survey.
        print(f"warning: lizard could not analyse {path}: {error}", file=sys.stderr)
        return metrics
    metrics.nloc = info.nloc
    for function in info.function_list:
        ccn = function.cyclomatic_complexity
        metrics.functions[function.long_name] = ccn
        metrics.worst_ccn = max(metrics.worst_ccn, ccn)
        metrics.functions_over_warn += ccn > CCN_WARN
        metrics.functions_over_crit += ccn > CCN_CRIT
        metrics.long_functions += function.length > LONG_FUNCTION
    return metrics


def churn_counts(days: int) -> Counter:
    log = git("log", f"--since={days}.days", "--no-merges", "--name-only", "--format=")
    return Counter(line for line in log.splitlines() if line.strip())


def survey(days: int, excludes: list[str]) -> list[FileMetrics]:
    root = repo_root()
    churn = churn_counts(days)
    files = []
    for path in git("ls-files").splitlines():
        if not analyzable(path, excludes):
            continue
        try:
            source = (root / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        metrics = measure(path, source)
        metrics.churn = churn.get(path, 0)
        files.append(metrics)
    score_hotspots(files)
    return files


def score_hotspots(files: list[FileMetrics]) -> None:
    # Tornhill's hotspot: change frequency times complexity, each normalised to the repo's maximum.
    max_churn = max((f.churn for f in files), default=0) or 1
    max_ccn = max((f.worst_ccn for f in files), default=0) or 1
    for f in files:
        f.hotspot = round((f.churn / max_churn) * (f.worst_ccn / max_ccn), 4)


def summary(files: list[FileMetrics]) -> dict[str, int]:
    production = [f for f in files if not f.test]
    return {
        "functions_over_ccn_warn": sum(f.functions_over_warn for f in production),
        "functions_over_ccn_crit": sum(f.functions_over_crit for f in production),
        "long_functions": sum(f.long_functions for f in production),
        "hotspot_files": sum(f.hotspot >= HOTSPOT_FILE_THRESHOLD and f.worst_ccn > CCN_WARN for f in production),
    }


def cmd_survey(args: argparse.Namespace) -> int:
    files = survey(args.days, args.exclude)
    hotspots = sorted((f for f in files if not f.test), key=lambda f: f.hotspot, reverse=True)[: args.top]
    if args.json:
        payload = {"summary": summary(files), "hotspots": [{k: v for k, v in asdict(f).items() if k != "functions"} for f in hotspots]}
        print(json.dumps(payload, indent=2))
        return 0
    print(f"Surveyed {len(files)} files, churn over the last {args.days} days.\n")
    for name, value in summary(files).items():
        print(f"  {name:<26} {value}")
    print(f"\n{'hotspot':>8} {'churn':>6} {'ccn':>5} {'nloc':>6}  path")
    for f in hotspots:
        print(f"{f.hotspot:>8.3f} {f.churn:>6} {f.worst_ccn:>5} {f.nloc:>6}  {f.path}")
    return 0


def worst_by_file(files: list[FileMetrics]) -> dict[str, int]:
    return {f.path: f.worst_ccn for f in files if not f.test and f.worst_ccn > CCN_CRIT}


def cmd_ratchet(args: argparse.Namespace) -> int:
    baseline_path = repo_root() / args.baseline
    files = survey(args.days, args.exclude)
    current = {"totals": summary(files), "worst_ccn_by_file": worst_by_file(files)}

    if args.action == "init" or not baseline_path.exists():
        if args.action != "init":
            print(f"No baseline at {args.baseline}; writing one from the current tree.")
        write_baseline(baseline_path, current)
        return 0

    baseline = load_baseline(baseline_path)
    violations = ratchet_violations(baseline, current)

    if args.action == "tighten":
        tightened = {
            "totals": {k: min(v, baseline["totals"].get(k, v)) for k, v in current["totals"].items()},
            "worst_ccn_by_file": {
                path: min(ccn, baseline["worst_ccn_by_file"].get(path, ccn))
                for path, ccn in current["worst_ccn_by_file"].items()
            },
        }
        if violations:
            print("Not tightening while ratchets are violated:")
            print_violations(violations)
            return 1
        write_baseline(baseline_path, tightened)
        return 0

    if violations:
        print_violations(violations)
        return 1
    print("All ratchets hold.")
    return 0


def ratchet_violations(baseline: dict, current: dict) -> list[str]:
    violations = []
    for key, value in current["totals"].items():
        allowed = baseline["totals"].get(key)
        if allowed is not None and value > allowed:
            violations.append(f"{key}: {value} (baseline {allowed})")
    for path, ccn in current["worst_ccn_by_file"].items():
        allowed = baseline["worst_ccn_by_file"].get(path)
        if allowed is None:
            violations.append(f"{path}: new function over CCN {CCN_CRIT} (worst {ccn})")
        elif ccn > allowed:
            violations.append(f"{path}: worst CCN {ccn} (baseline {allowed})")
    return violations


def print_violations(violations: list[str]) -> None:
    for violation in violations:
        print(f"  ratchet slipped: {violation}")


def write_baseline(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(f"Baseline written to {path}")


def changed_files(base: str) -> list[tuple[str, int, int]]:
    merge_base = merge_base_of(base)
    changes = []
    for line in git("diff", "--numstat", "--no-renames", merge_base).splitlines():
        try:
            added, deleted, path = line.split("\t", 2)
            if added == "-":
                continue
            changes.append((path, int(added), int(deleted)))
        except ValueError:
            print(f"warning: skipped an unreadable diff line: {line!r}", file=sys.stderr)
    return changes


def source_at(revision: str, path: str) -> str | None:
    result = subprocess.run(["git", "show", f"{revision}:{path}"], capture_output=True, text=True, errors="replace")
    return result.stdout if result.returncode == 0 else None


def cmd_risk(args: argparse.Namespace) -> int:
    root = repo_root()
    merge_base = merge_base_of(args.base)
    terrain = {f.path: f for f in survey(args.days, args.exclude)}
    changes = changed_files(args.base)

    source_lines = test_lines = 0
    complexity_added = 0
    worst_exposure = 0.0
    top_hotspot = max((f.hotspot for f in terrain.values() if not f.test), default=0.0) or 1.0
    areas = set()
    touched = []
    for path, added, deleted in changes:
        if not analyzable(path, args.exclude):
            continue
        areas.add(path.split("/")[0])
        if is_test(path):
            test_lines += added + deleted
            continue
        source_lines += added + deleted
        before = measure(path, source_at(merge_base, path) or "")
        after_path = root / path
        after = measure(path, after_path.read_text(encoding="utf-8", errors="replace")) if after_path.exists() else FileMetrics(path)
        # Complexity only counts above CCN_NOTABLE, so a dozen new one-line functions don't read as risk.
        delta = sum(
            max(0, ccn - max(before.functions.get(name, 0), CCN_NOTABLE)) for name, ccn in after.functions.items()
        )
        complexity_added += delta
        exposure = (terrain[path].hotspot / top_hotspot) if path in terrain else 0.0
        worst_exposure = max(worst_exposure, exposure)
        touched.append((path, added + deleted, exposure, delta, after.worst_ccn))

    factors = risk_factors(source_lines, test_lines, complexity_added, worst_exposure, len(areas))
    score = round(sum(weight * value for weight, value in factors.values()) * 100)
    level = "high" if score >= RISK_HIGH else "medium" if score >= RISK_MEDIUM else "low"

    baseline_path = root / args.baseline
    slipped = []
    if baseline_path.exists():
        current = {"totals": summary(list(terrain.values())), "worst_ccn_by_file": worst_by_file(list(terrain.values()))}
        slipped = ratchet_violations(load_baseline(baseline_path), current)

    report = render_risk(score, level, factors, touched, slipped, args.markdown)
    print(report)
    return 0


def risk_factors(source_lines: int, test_lines: int, complexity_added: int, exposure: float, areas: int) -> dict:
    # Each factor is squashed to 0..1. See reference/risk-model.md before changing them.
    size = min(1.0, math.log10(1 + source_lines) / SIZE_LOG_DECADES)
    untested = 0.0 if source_lines == 0 else max(0.0, 1 - test_lines / max(source_lines, 1))
    complexity = min(1.0, complexity_added / COMPLEXITY_SATURATION)
    hotspots = min(1.0, exposure)
    spread = min(1.0, (areas - 1) / SPREAD_SATURATION) if areas else 0.0
    values = {
        "change size": size,
        "hotspot exposure": hotspots,
        "complexity added": complexity,
        "missing test changes": untested,
        "spread across top-level areas": spread,
    }
    return {name: (WEIGHTS[name], value) for name, value in values.items()}


def render_risk(score: int, level: str, factors: dict, touched: list, slipped: list[str], markdown: bool) -> str:
    lines = [f"## Change risk: {score}/100 ({level})" if markdown else f"Change risk: {score}/100 ({level})", ""]
    lines.append("| factor | weight | value |" if markdown else "factors:")
    if markdown:
        lines.append("| --- | --- | --- |")
    for name, (weight, value) in factors.items():
        lines.append(f"| {name} | {weight:.2f} | {value:.2f} |" if markdown else f"  {name:<32} weight {weight:.2f}  value {value:.2f}")
    if slipped:
        lines += ["", "**Ratchets slipped**" if markdown else "ratchets slipped:"]
        lines += [f"- {s}" for s in slipped]
    riskiest = sorted(touched, key=lambda t: (t[2], t[3]), reverse=True)[:REVIEW_FIRST_LIMIT]
    if riskiest:
        lines += ["", "**Review these first**" if markdown else "review these first:"]
        for path, size, exposure, delta, worst in riskiest:
            lines.append(f"- `{path}`: {size} lines changed, hotspot {exposure:.2f}, +{delta} CCN, worst function {worst}")
    lines += ["", "_A triage aid, not a gate: the ratchets are the gate._" if markdown else "(triage aid, not a gate)"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="churn window in days")
    parser.add_argument("--exclude", action="append", default=list(DEFAULT_EXCLUDES), help="glob to skip, repeatable")
    parser.add_argument("--baseline", default=".lookout/ratchets.json")
    commands = parser.add_subparsers(dest="command", required=True)

    survey_parser = commands.add_parser("survey", help="hotspots and totals for the current tree")
    survey_parser.add_argument("--top", type=int, default=DEFAULT_TOP)
    survey_parser.add_argument("--json", action="store_true")
    survey_parser.set_defaults(run=cmd_survey)

    ratchet_parser = commands.add_parser("ratchet", help="hold or tighten the quality baseline")
    ratchet_parser.add_argument("action", choices=["init", "check", "tighten"])
    ratchet_parser.set_defaults(run=cmd_ratchet)

    risk_parser = commands.add_parser("risk", help="score the change between --base and HEAD plus the working tree")
    risk_parser.add_argument("--base", default="origin/main")
    risk_parser.add_argument("--markdown", action="store_true", help="format for a pull request comment")
    risk_parser.set_defaults(run=cmd_risk)

    args = parser.parse_args()
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
