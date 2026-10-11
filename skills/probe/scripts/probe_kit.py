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
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

# Hard limit of bot actions in one sweep run, so a bot that never returns None cannot loop forever.
MAX_SWEEP_ACTIONS = 500
DEFAULT_SEED = 1
# Printed when a replay refuses a recorded action; check_replay.py fails on this text.
REFUSED_ON_REPLAY = "warning: recorded action refused on replay"

VerbMethod = Callable[[Any, list[str]], str]


class Refused(Exception):
    """Raised by a verb that cannot run in the current state. Refused actions are never recorded."""


def verb(name: str, usage: str = "") -> Callable[[VerbMethod], VerbMethod]:
    def mark(method: VerbMethod) -> VerbMethod:
        method.verb_name = name  # type: ignore[attr-defined]
        method.verb_usage = usage  # type: ignore[attr-defined]
        return method
    return mark


class Harness(ABC):
    """Drive the real application through its user-facing entry points; never write its state directly."""

    def __init__(self) -> None:
        self.events: list[str] = []
        self.notes: list[str] = []

    @abstractmethod
    def boot(self, args: list[str], seed: int) -> None: ...

    @abstractmethod
    def view(self) -> str:
        """What a user would see right now, and nothing they couldn't."""

    def bot_action(self) -> str | None:
        """The next action of a simple policy for sweeps, or None when the run is over."""
        return None

    def outcome(self) -> dict[str, float]:
        """Numbers for report and sweep, e.g. orders placed, errors, time taken."""
        return {}

    def emit(self, event: str) -> None:
        self.events.append(event)

    def take_events(self) -> list[str]:
        events, self.events = self.events, []
        return events

    @classmethod
    def verbs(cls) -> dict[str, VerbMethod]:
        return {
            attribute.verb_name: attribute
            for klass in reversed(cls.__mro__)
            for attribute in vars(klass).values()
            if hasattr(attribute, "verb_name")
        }

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


HarnessType = type[Harness]
History = list[tuple[str, list[str]]]


def fail(message: str) -> NoReturn:
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


def start(harness_type: HarnessType, boot_tokens: list[str]) -> Harness:
    harness = harness_type()
    harness.boot(*parse_boot(boot_tokens))
    return harness


def read_session(session: Path) -> list[str]:
    if not session.is_file():
        fail(f"session file '{session}' does not exist. Start one with: new {session} <boot args...>")
    lines = [line for line in session.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines or not lines[0].startswith("boot"):
        fail(f"session file '{session}' has no boot line. Start a new session.")
    return lines


def replay_action(harness: Harness, line: str) -> list[str]:
    try:
        harness.act(line)
    except Refused as refusal:
        print(f"{REFUSED_ON_REPLAY} ({refusal}); the build no longer matches this session")
    return harness.take_events()


def replay(harness_type: HarnessType, session: Path) -> tuple[Harness, History]:
    boot_line, *actions = read_session(session)
    harness = start(harness_type, shlex.split(boot_line)[1:])
    history: History = [("boot", harness.take_events())]
    history += [(line, replay_action(harness, line)) for line in actions]
    return harness, history


@dataclass(frozen=True)
class Run:
    harness_type: HarnessType
    session: Path
    args: list[str]


def run_bot(harness: Harness, max_actions: int) -> dict[str, float]:
    for _ in range(max_actions):
        action = harness.bot_action()
        if action is None:
            break
        try:
            harness.act(action)
        except Refused:
            break
    return harness.outcome()


def sweep(harness_type: HarnessType, boot_args: list[str], runs: int, max_actions: int = MAX_SWEEP_ACTIONS) -> None:
    results = []
    for seed in range(1, runs + 1):
        harness = harness_type()
        harness.boot(boot_args, seed)
        results.append(run_bot(harness, max_actions))
    print(f"{runs} runs, seeds 1..{runs}")
    for key in sorted({key for result in results for key in result}):
        values = [result.get(key, 0) for result in results]
        print(f"  {key:<24} mean {statistics.mean(values):8.2f}  min {min(values):8.2f}  max {max(values):8.2f}")


def command_new(run: Run) -> int:
    harness = start(run.harness_type, run.args)
    run.session.write_text(shlex.join(["boot", *run.args]) + "\n", encoding="utf-8")
    print("\n".join(harness.events))
    print(harness.view())
    return 0


def act_and_print(harness: Harness, line: str) -> bool:
    try:
        summary = harness.act(line)
    except Refused as refusal:
        print(f"refused: {line}: {refusal}")
        return False
    for event in harness.take_events():
        print(f"  {event}")
    print(f"> {line}: {summary}")
    return True


def command_do(run: Run) -> int:
    harness, _ = replay(run.harness_type, run.session)
    accepted = []
    for line in run.args:
        if not act_and_print(harness, line):
            break
        accepted.append(line)
    with run.session.open("a", encoding="utf-8") as handle:
        handle.writelines(line + "\n" for line in accepted)
    print()
    print(harness.view())
    return 0


def command_look(run: Run) -> int:
    harness, _ = replay(run.harness_type, run.session)
    print(harness.view())
    return 0


def command_log(run: Run) -> int:
    _, history = replay(run.harness_type, run.session)
    for line, events in history:
        print(f"> {line}")
        print("".join(f"  {event}\n" for event in events), end="")
    return 0


def command_report(run: Run) -> int:
    harness, _ = replay(run.harness_type, run.session)
    for key, value in harness.outcome().items():
        print(f"{key:<24} {value}")
    if harness.notes:
        print("\nnotes:")
        print("".join(f"- {note}\n" for note in harness.notes), end="")
    return 0


SESSION_COMMANDS: dict[str, Callable[[Run], int]] = {
    "new": command_new,
    "do": command_do,
    "look": command_look,
    "log": command_log,
    "report": command_report,
}


def command_sweep(harness_type: HarnessType, rest: list[str]) -> int:
    if len(rest) < 2 or rest[-2] != "runs":
        print("usage: sweep <boot args...> runs N")
        return 2
    sweep(harness_type, rest[:-2], parse_int(rest[-1], "runs"))
    return 0


def main(harness_type: HarnessType) -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    command, rest = sys.argv[1], sys.argv[2:]
    if command == "sweep":
        return command_sweep(harness_type, rest)
    if not rest:
        print(f"usage: {command} <session file> ...")
        return 2
    handler = SESSION_COMMANDS.get(command)
    if handler is None:
        print(f"unknown command '{command}'")
        return 2
    return handler(Run(harness_type, Path(rest[0]), rest[1:]))
