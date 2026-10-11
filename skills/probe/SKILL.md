---
name: probe
description: Builds a headless text tool that drives an application through its real entry points and saves each session as a replayable action log. Use when the user asks to try out a change, explore a flow, reproduce a bug exactly, or measure how a feature behaves across seeds.
---

# Probe

## Purpose

An agent that only reads code and runs unit tests cannot see if a change works. It can only guess, as a reviewer does.

A **probe** is a small headless tool. With a probe, an agent uses the application as a user does: it acts, looks, and acts again. Each finding comes with an exact reproduction.

Every probe obeys four rules. Together, they go through the entry point of the application and report only what a user can see:

- **Every action is user input.** A verb never writes application state. A verb calls what a user action calls: the HTTP endpoint, the command handler, or the UI input layer. When a verb must select a target, the lookup of the application selects it.
- **The view shows only what the user sees.** If the user cannot see a field, an error or a record, the view does not show it. Feedback on information that the user never gets is wrong feedback.
- **A session is its action log.** The session file holds one boot line and every accepted action. Each call replays the session file from the start.
- **The probe emulates side effects. It does not skip them.** Payments, email, queues and storage go to fakes. The fakes behave like the real services, failures included, and decide with a seeded generator. Skipped side effects hide the paths that users hit.

A probe cannot show visual layout, animation, accessibility, real-time behaviour, latency under load, or behaviour that needs a real outside service.

## The contract

The contract does not depend on a language: the commands `new`, `do`, `look`, `log`, `report` and `sweep`, the `note` verb, the session file format, a replay on every call, and refusals that are never recorded. [reference/design.md](reference/design.md) defines it.

## Workflow: build a probe

Use this workflow when the application has no probe.

```
- [ ] 1. Find entry points and choose the language
- [ ] 2. Make the application deterministic
- [ ] 3. Write the boot, the view and three verbs
- [ ] 4. Add events, interrupts and the report
- [ ] 5. Add a test for the probe
- [ ] 6. Document the verbs
```

1. Find the entry point. Name the entry points that user actions go through. Name the screen or response that the user reads. The probe touches only these. The only exception is the debug command in reference/design.md.
   Write the probe in the language of the application. Drive the in-process entry point that the tests of the application use, such as `MockMvc` for Spring, `TestClient` for FastAPI, or the simulation step of a game. Build it with the build of the project.
   Use `probe_kit.py` only when the application is in Python, or when the network is the only way to reach it. In any other language, port the shape of the kit. Read [reference/porting.md](reference/porting.md).
2. Make the application deterministic before you write a verb. Inject the clock. Seed every random generator. Make identifiers sequential. Replace every outside call with a seeded fake.
   If the application is not deterministic, make it deterministic before you continue. The probe found a testability problem.
   Add a replay test. Run `check_replay.py` against the probe command, in any language. In the test suite of the project, add a test that replays one session two times and compares the output.
3. Write the boot, the view and three verbs. Use the smallest loop that a user does. Play the loop one time yourself. Change the view until it reads like the screen.
4. Add events and interrupts. Then add `report`. Add a sweep bot only when somebody needs numbers.
5. Add a test that boots the probe, runs a short session through the probe library and checks the outcome.
6. Document the verbs in a table. Write the table so that a future agent can use it after one reading.

## Workflow: probe a change

Use this workflow when the user wants a change tried out, a flow explored, or a bug reproduced.

1. Start one session for each question. Put the session file in a scratch directory, not in the repository.
2. Play as a first-time user. Read all of the view. Try the obvious route before the clever route. Use `note` each time you must guess.
3. Report the findings in order of impact. Give the evidence for each finding: event lines and report numbers.
4. Include the content of the session file that reproduces each finding.
5. Say so when a finding depends on something that a probe cannot show.

## Workflow: sweep

Use this workflow when the user wants to know how a feature behaves across many runs.

1. Run `sweep` before and after the change, with the same seeds.
2. Compare the two results. The bot is simple on purpose. Its numbers are a floor, not a forecast.

## Reference files

- Before you build a probe, read [reference/design.md](reference/design.md).
- Before you build a probe in a language other than Python, read [reference/porting.md](reference/porting.md).
- Before you credit the method or explain where its ideas come from, read [reference/sources.md](reference/sources.md).

## Scripts

All scripts need Python 3 and no other packages. They are the reference implementation of the contract, not the default language of a probe.

- READ [scripts/probe_kit.py](scripts/probe_kit.py) before you build a probe in Python, and before you port the kit to another language. Subclass `Harness`. Implement `boot`, `view` and a few `@verb`s. `bot_action` and `outcome` are optional. The kit gives `new`, `do`, `look`, `log`, `report` and `sweep`, a replay on every call, refusals that are never recorded, and a built-in `note` verb.
- READ [scripts/example_shop_probe.py](scripts/example_shop_probe.py) and copy from it. It is a complete probe for a small shop, with an injected clock, seeded payment declines and cart expiry.
- RUN `python scripts/check_replay.py <session file> -- <probe command...>` to prove that any probe replays deterministically, for example `-- java -jar build/probe.jar`. It replays the session two times and compares the output.
