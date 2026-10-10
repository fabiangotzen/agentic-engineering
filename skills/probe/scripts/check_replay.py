#!/usr/bin/env python3
"""Prove that a probe built on probe_kit replays deterministically.

    python scripts/check_replay.py <probe script> <session file>

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
# Seconds one replay may take before the check reports it as hung.
TIMEOUT_SECONDS = 300
# Number of differing lines shown when two replays do not match.
DIFF_LINES = 40


def run(probe: Path, command: str, session: Path) -> str:
    try:
        result = subprocess.run(
            [sys.executable, str(probe), command, str(session)],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        sys.exit(f"error: '{command}' did not finish within {TIMEOUT_SECONDS} seconds.")
    if result.returncode != 0:
        sys.exit(f"error: '{command}' failed with exit code {result.returncode}:\n{result.stderr.strip()}")
    return result.stdout + result.stderr


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    probe, session = Path(sys.argv[1]), Path(sys.argv[2])
    if not probe.is_file():
        print(f"error: probe script '{probe}' does not exist.")
        return 2
    if not session.is_file():
        print(f"error: session file '{session}' does not exist.")
        return 2

    for command in REPLAY_COMMANDS:
        first, second = run(probe, command, session), run(probe, command, session)
        if first != second:
            print(f"FAIL: two replays of '{command}' differ. The probe is not deterministic.")
            diff = difflib.unified_diff(first.splitlines(), second.splitlines(), "replay 1", "replay 2", lineterm="")
            print("\n".join(list(diff)[:DIFF_LINES]))
            return 1
        print(f"PASS: '{command}' is identical across two replays ({len(first.splitlines())} lines).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
