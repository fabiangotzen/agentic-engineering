#!/usr/bin/env python3
"""Check that a probe session replays the same way two times, in any language.

    python scripts/check_replay.py <session file> -- <probe command...>
    python scripts/check_replay.py <probe script.py> <session file>

The probe command is run as `<probe command...> look <session file>`, so any probe that follows the
contract works: a kit script, a jar, or a native binary. The second form is short for a kit probe.
Fails when a replay refuses a recorded action. Two matching runs show that this session repeats; they do
not prove that the application is deterministic everywhere.

Replays the session two times through the probe's `look` and `log` commands and compares the output byte
for byte. Exits 0 when both replays match, 1 when they differ, 2 on a usage or run error.

Requires Python 3 and no other packages. The session file is read, never written.
"""

from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

REPLAY_COMMANDS = ("look", "log")
# Part of the probe contract: every probe prints this text when a replay refuses a recorded action.
REFUSED_ON_REPLAY = "warning: recorded action refused on replay"
TIMEOUT_SECONDS = 300
DIFF_LINES = 40


class UsageError(Exception):
    """A bad command line or a missing file; reported with exit code 2."""


def run(probe: list[str], command: str, session: Path) -> str:
    try:
        result = subprocess.run(
            [*probe, command, str(session)],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False,
        )
    except subprocess.TimeoutExpired:
        raise UsageError(f"error: '{command}' did not finish within {TIMEOUT_SECONDS} seconds.") from None
    except OSError as error:
        raise UsageError(f"error: cannot start the probe command {probe}: {error}") from None
    if result.returncode != 0:
        raise UsageError(f"error: '{command}' failed with exit code {result.returncode}:\n{result.stderr.strip()}")
    return result.stdout + result.stderr


def parse_args(args: list[str]) -> tuple[Path, list[str]]:
    if len(args) >= 3 and args[1] == "--":
        return Path(args[0]), args[2:]
    if len(args) != 2:
        raise UsageError(__doc__ or "")
    script = Path(args[0])
    if not script.is_file():
        raise UsageError(f"error: probe script '{script}' does not exist.")
    return Path(args[1]), [sys.executable, str(script)]


def compare(command: str, first: str, second: str) -> list[str]:
    """The lines that explain a failure, or an empty list when the two replays pass."""
    if REFUSED_ON_REPLAY in first:
        refused = [line for line in first.splitlines() if REFUSED_ON_REPLAY in line]
        return [f"FAIL: '{command}' refused a recorded action. The session no longer matches the build.", *refused]
    if first != second:
        diff = difflib.unified_diff(first.splitlines(), second.splitlines(), "replay 1", "replay 2", lineterm="")
        return [f"FAIL: two replays of '{command}' differ. This session does not repeat.", *list(diff)[:DIFF_LINES]]
    return []


def check(session: Path, probe: list[str]) -> int:
    if not session.is_file():
        raise UsageError(f"error: session file '{session}' does not exist.")
    for command in REPLAY_COMMANDS:
        first = run(probe, command, session)
        failure = compare(command, first, run(probe, command, session))
        if failure:
            print("\n".join(failure))
            return 1
        print(f"PASS: '{command}' is identical across two replays ({len(first.splitlines())} lines).")
    return 0


def main(argv: list[str]) -> int:
    try:
        return check(*parse_args(argv[1:]))
    except UsageError as error:
        print(error)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
