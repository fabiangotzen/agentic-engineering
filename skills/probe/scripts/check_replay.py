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

# Commands that replay the whole session without adding an action to it.
REPLAY_COMMANDS = ("look", "log")
# The line a probe prints when a replay refuses a recorded action; part of the probe contract.
REFUSED_ON_REPLAY = "warning: recorded action refused on replay"
# Seconds one replay may take before the check reports it as hung.
TIMEOUT_SECONDS = 300
# Number of differing lines shown when two replays do not match.
DIFF_LINES = 40


def run(probe: list[str], command: str, session: Path) -> str:
    try:
        result = subprocess.run(
            [*probe, command, str(session)],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        sys.exit(f"error: '{command}' did not finish within {TIMEOUT_SECONDS} seconds.")
    if result.returncode != 0:
        sys.exit(f"error: '{command}' failed with exit code {result.returncode}:\n{result.stderr.strip()}")
    return result.stdout + result.stderr


def main() -> int:
    args = sys.argv[1:]
    if len(args) >= 3 and args[1] == "--":
        session, probe = Path(args[0]), args[2:]
    elif len(args) == 2:
        script, session = Path(args[0]), Path(args[1])
        if not script.is_file():
            print(f"error: probe script '{script}' does not exist.")
            return 2
        probe = [sys.executable, str(script)]
    else:
        print(__doc__)
        return 2
    if not session.is_file():
        print(f"error: session file '{session}' does not exist.")
        return 2

    for command in REPLAY_COMMANDS:
        first, second = run(probe, command, session), run(probe, command, session)
        if REFUSED_ON_REPLAY in first:
            print(f"FAIL: '{command}' refused a recorded action. The session no longer matches the build.")
            print("\n".join(line for line in first.splitlines() if REFUSED_ON_REPLAY in line))
            return 1
        if first != second:
            print(f"FAIL: two replays of '{command}' differ. This session does not repeat.")
            diff = difflib.unified_diff(first.splitlines(), second.splitlines(), "replay 1", "replay 2", lineterm="")
            print("\n".join(list(diff)[:DIFF_LINES]))
            return 1
        print(f"PASS: '{command}' is identical across two replays ({len(first.splitlines())} lines).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
