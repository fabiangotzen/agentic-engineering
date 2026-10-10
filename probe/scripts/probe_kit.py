#!/usr/bin/env python3
"""A minimal kit for headless probes: subclass Harness, get the session CLI for free.

    python my_probe.py new  s.probe <boot args...> [seed N]   # start a session
    python my_probe.py do   s.probe "verb args" "verb args"   # act; prints events, summaries, then the view
    python my_probe.py look s.probe                           # the view again, without acting
    python my_probe.py log  s.probe                           # every event, action by action
    python my_probe.py report s.probe                         # outcome numbers and your notes
    python my_probe.py sweep <boot args...> runs 20           # the bot plays seeds 1..20

A session file is its boot line plus every accepted action. Each call replays it from scratch, so the
harness must be deterministic: inject the clock, seed the randomness, fake the outside world.

Requires Python 3 and no other packages.
"""

from __future__ import annotations

import shlex
import statistics
import sys
from pathlib import Path
from typing import Callable

# Hard limit of bot actions in one sweep run, so a bot that never returns None cannot loop forever.
MAX_SWEEP_ACTIONS = 500
# Seed used when the boot line has no "seed N".
DEFAULT_SEED = 1


class Refused(Exception):
    """Raised by a verb that cannot run in the current state. Refused actions are never recorded."""


def verb(name: str, usage: str = "") -> Callable:
    def mark(method: Callable) -> Callable:
        method.verb_name = name
        method.verb_usage = usage
        return method
    return mark


class Harness:
    """Drive the real application through its user-facing entry points; never write its state directly."""

    def boot(self, args: list[str], seed: int) -> None:
        raise NotImplementedError

    def view(self) -> str:
        """What a user would see right now, and nothing they couldn't."""
        raise NotImplementedError

    def bot_action(self) -> str | None:
        """The next action of a simple policy for sweeps, or None when the run is over."""
        return None

    def outcome(self) -> dict[str, float]:
        """Numbers for report and sweep, e.g. orders placed, errors, time taken."""
        return {}

    def __init__(self) -> None:
        self.events: list[str] = []
        self.notes: list[str] = []

    def emit(self, event: str) -> None:
        self.events.append(event)

    @classmethod
    def verbs(cls) -> dict[str, Callable]:
        found = {}
        for klass in reversed(cls.__mro__):
            for attribute in vars(klass).values():
                if hasattr(attribute, "verb_name"):
                    found[attribute.verb_name] = attribute
        return found

    @verb("note", "text")
    def note(self, args: list[str]) -> str:
        self.notes.append(" ".join(args))
        return "noted"

    def act(self, line: str) -> str:
        name, *args = shlex.split(line)
        method = self.verbs().get(name)
        if method is None:
            raise Refused(f"unknown verb '{name}'. Verbs: {', '.join(sorted(self.verbs()))}")
        return method(self, args)


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(2)


def parse_int(text: str, what: str) -> int:
    try:
        return int(text)
    except ValueError:
        fail(f"{what} must be a whole number, got '{text}'")


def parse_boot(tokens: list[str]) -> tuple[list[str], int]:
    if len(tokens) >= 2 and tokens[-2] == "seed":
        return tokens[:-2], parse_int(tokens[-1], "seed")
    return tokens, DEFAULT_SEED


def replay(harness_type: type[Harness], session: Path) -> tuple[Harness, list[tuple[str, list[str]]]]:
    if not session.is_file():
        fail(f"session file '{session}' does not exist. Start one with: new {session} <boot args...>")
    lines = [line for line in session.read_text().splitlines() if line.strip()]
    if not lines or not lines[0].startswith("boot"):
        fail(f"session file '{session}' has no boot line. Start a new session.")
    boot_args, seed = parse_boot(shlex.split(lines[0])[1:])
    harness = harness_type()
    harness.boot(boot_args, seed)
    history = [("boot", harness.events[:])]
    for line in lines[1:]:
        harness.events.clear()
        try:
            harness.act(line)
        except Refused as refusal:
            print(f"warning: recorded action refused on replay ({refusal}); the build no longer matches this session")
        history.append((line, harness.events[:]))
    harness.events.clear()
    return harness, history


def sweep(harness_type: type[Harness], boot_args: list[str], runs: int, max_actions: int = MAX_SWEEP_ACTIONS) -> None:
    results = []
    for seed in range(1, runs + 1):
        harness = harness_type()
        harness.boot(boot_args, seed)
        for _ in range(max_actions):
            action = harness.bot_action()
            if action is None:
                break
            try:
                harness.act(action)
            except Refused:
                break
        results.append(harness.outcome())
    keys = sorted({key for result in results for key in result})
    print(f"{runs} runs, seeds 1..{runs}")
    for key in keys:
        values = [result.get(key, 0) for result in results]
        print(f"  {key:<24} mean {statistics.mean(values):8.2f}  min {min(values):8.2f}  max {max(values):8.2f}")


def main(harness_type: type[Harness]) -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    command, rest = sys.argv[1], sys.argv[2:]

    if command == "sweep":
        if len(rest) < 2 or rest[-2] != "runs":
            print("usage: sweep <boot args...> runs N")
            return 2
        sweep(harness_type, rest[:-2], parse_int(rest[-1], "runs"))
        return 0

    if not rest:
        print(f"usage: {command} <session file> ...")
        return 2
    session = Path(rest[0])

    if command == "new":
        harness = harness_type()
        boot_args, seed = parse_boot(rest[1:])
        harness.boot(boot_args, seed)
        session.write_text(shlex.join(["boot", *rest[1:]]) + "\n")
        print("\n".join(harness.events))
        print(harness.view())
        return 0

    harness, history = replay(harness_type, session)

    if command == "do":
        accepted = []
        for line in rest[1:]:
            try:
                summary = harness.act(line)
            except Refused as refusal:
                print(f"refused: {line}: {refusal}")
                break
            accepted.append(line)
            for event in harness.events:
                print(f"  {event}")
            harness.events.clear()
            print(f"> {line}: {summary}")
        with session.open("a") as handle:
            handle.writelines(line + "\n" for line in accepted)
        print()
        print(harness.view())
        return 0
    if command == "look":
        print(harness.view())
        return 0
    if command == "log":
        for line, events in history:
            print(f"> {line}")
            print("".join(f"  {event}\n" for event in events), end="")
        return 0
    if command == "report":
        for key, value in harness.outcome().items():
            print(f"{key:<24} {value}")
        if harness.notes:
            print("\nnotes:")
            print("".join(f"- {note}\n" for note in harness.notes), end="")
        return 0

    print(f"unknown command '{command}'")
    return 2
