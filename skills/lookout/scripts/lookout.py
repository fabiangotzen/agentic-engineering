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
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

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
# Heuristic risk score from which a sighting is high, and from which it is medium.
RISK_HIGH = 60
RISK_MEDIUM = 30
# Complexity added at which the complexity factor reaches 1.
COMPLEXITY_SATURATION = 30
# Orders of magnitude of changed lines at which the size factor reaches 1 (3 means 1,000 lines).
SIZE_LOG_DECADES = 3
# Extra top-level areas at which the spread factor reaches 1.
SPREAD_SATURATION = 4
REVIEW_FIRST_LIMIT = 8
# Factor weights; they sum to 1. Read reference/risk-model.md before changing them.
WEIGHTS = {
    "change size": 0.20,
    "hotspot exposure": 0.30,
    "complexity added": 0.25,
    "missing test changes": 0.15,
    "spread across top-level areas": 0.10,
}
DEFAULT_DAYS = 90
DEFAULT_TOP = 15
DEFAULT_BASELINE = ".lookout/ratchets.json"


# --- git ---------------------------------------------------------------------------------------------------


def git(*args: str) -> str:
    """Stdout of a git command, or an empty string when it fails."""
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
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


def source_at(revision: str, path: str) -> str:
    return git("show", f"{revision}:{path}")


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# --- measuring files ---------------------------------------------------------------------------------------


def is_test(path: str) -> bool:
    return any(marker in part for part in path.lower().split("/") for marker in TEST_MARKERS)


def analyzable(path: str, excludes: list[str]) -> bool:
    if get_reader_for(path) is None:
        return False
    return not any(fnmatch.fnmatch("/" + path, pattern) for pattern in excludes)


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

    def add_function(self, name: str, ccn: int, length: int) -> None:
        self.functions[name] = ccn
        self.worst_ccn = max(self.worst_ccn, ccn)
        self.functions_over_warn += ccn > CCN_WARN
        self.functions_over_crit += ccn > CCN_CRIT
        self.long_functions += length > LONG_FUNCTION


def measure(path: str, source: str) -> FileMetrics:
    metrics = FileMetrics(path=path, test=is_test(path))
    try:
        info = lizard.analyze_file.analyze_source_code(path, source)
    except Exception as error:  # lizard can fail on unusual syntax; one file must not stop the survey.
        print(f"warning: lizard could not analyse {path}: {error}", file=sys.stderr)
        return metrics
    metrics.nloc = info.nloc
    for function in info.function_list:
        metrics.add_function(function.long_name, function.cyclomatic_complexity, function.length)
    return metrics


def churn_counts(days: int) -> Counter[str]:
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
            metrics = measure(path, read_source(root / path))
        except OSError:
            continue
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


def production(files: list[FileMetrics]) -> list[FileMetrics]:
    return [f for f in files if not f.test]


def top_hotspots(files: list[FileMetrics], count: int) -> list[FileMetrics]:
    return sorted(production(files), key=lambda f: f.hotspot, reverse=True)[:count]


# --- survey ------------------------------------------------------------------------------------------------


def summary(files: list[FileMetrics]) -> dict[str, int]:
    kept = production(files)
    return {
        "functions_over_ccn_warn": sum(f.functions_over_warn for f in kept),
        "functions_over_ccn_crit": sum(f.functions_over_crit for f in kept),
        "long_functions": sum(f.long_functions for f in kept),
        "hotspot_files": sum(f.hotspot >= HOTSPOT_FILE_THRESHOLD and f.worst_ccn > CCN_WARN for f in kept),
    }


def survey_json(files: list[FileMetrics], hotspots: list[FileMetrics]) -> str:
    rows = [{key: value for key, value in asdict(f).items() if key != "functions"} for f in hotspots]
    return json.dumps({"summary": summary(files), "hotspots": rows}, indent=2)


def survey_text(files: list[FileMetrics], hotspots: list[FileMetrics], days: int) -> str:
    lines = [f"Surveyed {len(files)} files, churn over the last {days} days.", ""]
    lines += [f"  {name:<26} {value}" for name, value in summary(files).items()]
    lines += ["", f"{'hotspot':>8} {'churn':>6} {'ccn':>5} {'nloc':>6}  path"]
    lines += [f"{f.hotspot:>8.3f} {f.churn:>6} {f.worst_ccn:>5} {f.nloc:>6}  {f.path}" for f in hotspots]
    return "\n".join(lines)


def cmd_survey(args: argparse.Namespace) -> int:
    files = survey(args.days, args.exclude)
    hotspots = top_hotspots(files, args.top)
    print(survey_json(files, hotspots) if args.json else survey_text(files, hotspots, args.days))
    return 0


# --- ratchets ----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Snapshot:
    """The ratcheted numbers: totals, and the worst function of each file over CCN_CRIT."""

    totals: dict[str, int]
    worst_ccn_by_file: dict[str, int]

    @classmethod
    def of(cls, files: list[FileMetrics]) -> Snapshot:
        worst = {f.path: f.worst_ccn for f in production(files) if f.worst_ccn > CCN_CRIT}
        return cls(summary(files), worst)

    def tightened(self, baseline: Snapshot) -> Snapshot:
        totals = {key: min(value, baseline.totals.get(key, value)) for key, value in self.totals.items()}
        worst = {
            path: min(ccn, baseline.worst_ccn_by_file.get(path, ccn)) for path, ccn in self.worst_ccn_by_file.items()
        }
        return Snapshot(totals, worst)

    def violations(self, baseline: Snapshot) -> list[str]:
        found = [
            f"{key}: {value} (baseline {baseline.totals[key]})"
            for key, value in self.totals.items()
            if key in baseline.totals and value > baseline.totals[key]
        ]
        for path, ccn in self.worst_ccn_by_file.items():
            allowed = baseline.worst_ccn_by_file.get(path)
            if allowed is None:
                found.append(f"{path}: new function over CCN {CCN_CRIT} (worst {ccn})")
            elif ccn > allowed:
                found.append(f"{path}: worst CCN {ccn} (baseline {allowed})")
        return found


def load_baseline(path: Path) -> Snapshot:
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return Snapshot(dict(data["totals"]), dict(data["worst_ccn_by_file"]))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        sys.exit(f"error: cannot read the baseline {path}: {error}. Fix the file or run 'ratchet init'.")


def write_baseline(path: Path, snapshot: Snapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(snapshot), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Baseline written to {path}")


def print_violations(violations: list[str]) -> None:
    for violation in violations:
        print(f"  ratchet slipped: {violation}")


def ratchet_check(path: Path, current: Snapshot) -> int:
    violations = current.violations(load_baseline(path))
    if violations:
        print_violations(violations)
        return 1
    print("All ratchets hold.")
    return 0


def ratchet_tighten(path: Path, current: Snapshot) -> int:
    baseline = load_baseline(path)
    violations = current.violations(baseline)
    if violations:
        print("Not tightening while ratchets are violated:")
        print_violations(violations)
        return 1
    write_baseline(path, current.tightened(baseline))
    return 0


def cmd_ratchet(args: argparse.Namespace) -> int:
    path = repo_root() / args.baseline
    current = Snapshot.of(survey(args.days, args.exclude))
    if args.action == "init":
        write_baseline(path, current)
        return 0
    if not path.exists():
        print(f"error: no baseline at {args.baseline}. Run 'ratchet init' and commit the file.")
        return 1
    return ratchet_tighten(path, current) if args.action == "tighten" else ratchet_check(path, current)


# --- risk --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TouchedFile:
    path: str
    lines: int
    exposure: float
    complexity_added: int
    worst_ccn: int


@dataclass
class Change:
    source_lines: int = 0
    test_lines: int = 0
    areas: set[str] = field(default_factory=set)
    touched: list[TouchedFile] = field(default_factory=list)

    @property
    def complexity_added(self) -> int:
        return sum(t.complexity_added for t in self.touched)

    @property
    def worst_exposure(self) -> float:
        return max((t.exposure for t in self.touched), default=0.0)


@dataclass(frozen=True)
class Factor:
    name: str
    weight: float
    value: float


def changed_files(merge_base: str) -> list[tuple[str, int, int]]:
    changes = []
    for line in git("diff", "--numstat", "--no-renames", merge_base).splitlines():
        try:
            added, deleted, path = line.split("\t", 2)
            if added != "-":
                changes.append((path, int(added), int(deleted)))
        except ValueError:
            print(f"warning: skipped an unreadable diff line: {line!r}", file=sys.stderr)
    return changes


def complexity_added(before: FileMetrics, after: FileMetrics) -> int:
    # Complexity only counts above CCN_NOTABLE, so a dozen new one-line functions don't read as risk.
    return sum(
        max(0, ccn - max(before.functions.get(name, 0), CCN_NOTABLE)) for name, ccn in after.functions.items()
    )


@dataclass(frozen=True)
class RiskContext:
    root: Path
    merge_base: str
    files: dict[str, FileMetrics]
    top_hotspot: float

    def touch(self, path: str, lines: int) -> TouchedFile:
        before = measure(path, source_at(self.merge_base, path))
        current = self.root / path
        after = measure(path, read_source(current)) if current.exists() else FileMetrics(path)
        exposure = self.files[path].hotspot / self.top_hotspot if path in self.files else 0.0
        return TouchedFile(path, lines, exposure, complexity_added(before, after), after.worst_ccn)


def measure_change(context: RiskContext, excludes: list[str]) -> Change:
    change = Change()
    for path, added, deleted in changed_files(context.merge_base):
        if not analyzable(path, excludes):
            continue
        change.areas.add(path.split("/")[0])
        if is_test(path):
            change.test_lines += added + deleted
        else:
            change.source_lines += added + deleted
            change.touched.append(context.touch(path, added + deleted))
    return change


def risk_factors(change: Change) -> list[Factor]:
    # Each factor is squashed to 0..1. See reference/risk-model.md before changing them.
    source, areas = change.source_lines, len(change.areas)
    values = {
        "change size": min(1.0, math.log10(1 + source) / SIZE_LOG_DECADES),
        "hotspot exposure": min(1.0, change.worst_exposure),
        "complexity added": min(1.0, change.complexity_added / COMPLEXITY_SATURATION),
        "missing test changes": max(0.0, 1 - change.test_lines / source) if source else 0.0,
        "spread across top-level areas": min(1.0, (areas - 1) / SPREAD_SATURATION) if areas else 0.0,
    }
    return [Factor(name, WEIGHTS[name], value) for name, value in values.items()]


def risk_level(score: int) -> str:
    if score >= RISK_HIGH:
        return "high"
    return "medium" if score >= RISK_MEDIUM else "low"


@dataclass(frozen=True)
class RiskReport:
    factors: list[Factor]
    touched: list[TouchedFile]
    slipped: list[str]

    @property
    def score(self) -> int:
        return round(sum(f.weight * f.value for f in self.factors) * 100)

    def review_first(self) -> list[TouchedFile]:
        ranked = sorted(self.touched, key=lambda t: (t.exposure, t.complexity_added), reverse=True)
        return ranked[:REVIEW_FIRST_LIMIT]


@dataclass(frozen=True)
class Style:
    title: str
    factor_header: list[str]
    factor_row: str
    slipped: str
    review: str
    footer: str


TEXT = Style(
    title="Change risk: {score}/100 ({level})",
    factor_header=["factors:"],
    factor_row="  {name:<32} weight {weight:.2f}  value {value:.2f}",
    slipped="ratchets slipped:",
    review="review these first:",
    footer="(triage aid, not a gate)",
)
MARKDOWN = Style(
    title="## Change risk: {score}/100 ({level})",
    factor_header=["| factor | weight | value |", "| --- | --- | --- |"],
    factor_row="| {name} | {weight:.2f} | {value:.2f} |",
    slipped="**Ratchets slipped**",
    review="**Review these first**",
    footer="_A triage aid, not a gate: the ratchets are the gate._",
)


def render_risk(report: RiskReport, style: Style) -> str:
    lines = [style.title.format(score=report.score, level=risk_level(report.score)), "", *style.factor_header]
    lines += [style.factor_row.format(**asdict(factor)) for factor in report.factors]
    if report.slipped:
        lines += ["", style.slipped, *(f"- {slip}" for slip in report.slipped)]
    riskiest = report.review_first()
    if riskiest:
        lines += ["", style.review]
        lines += [
            f"- `{t.path}`: {t.lines} lines changed, hotspot {t.exposure:.2f}, "
            f"+{t.complexity_added} CCN, worst function {t.worst_ccn}"
            for t in riskiest
        ]
    lines += ["", style.footer]
    return "\n".join(lines)


def slipped_ratchets(baseline_path: Path, files: list[FileMetrics]) -> list[str]:
    if not baseline_path.exists():
        return []
    return Snapshot.of(files).violations(load_baseline(baseline_path))


def cmd_risk(args: argparse.Namespace) -> int:
    root = repo_root()
    merge_base = merge_base_of(args.base)
    files = survey(args.days, args.exclude)
    top_hotspot = max((f.hotspot for f in production(files)), default=0.0) or 1.0
    context = RiskContext(root, merge_base, {f.path: f for f in files}, top_hotspot)
    change = measure_change(context, args.exclude)
    report = RiskReport(risk_factors(change), change.touched, slipped_ratchets(root / args.baseline, files))
    print(render_risk(report, MARKDOWN if args.markdown else TEXT))
    return 0


# --- command line ------------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="churn window in days")
    parser.add_argument("--exclude", action="append", default=list(DEFAULT_EXCLUDES), help="glob to skip, repeatable")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run: Callable[[argparse.Namespace], int] = args.run
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
