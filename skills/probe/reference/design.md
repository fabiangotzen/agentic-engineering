# Designing a probe

This file describes the parts of a probe, the session file, determinism, the view, verbs, sweeps and maintenance.

## Parts

| Part                 | Content                                                                                                      |
|----------------------|--------------------------------------------------------------------------------------------------------------|
| **Boot**             | Starts the application in a named state, such as a fixture, a checkpoint or a seeded dataset, with a seed.   |
| **Verbs**            | User-sized actions (`add mug 2`, `checkout`, `wait 45`). Each verb runs until it is done or interrupted.     |
| **View**             | The text observation: what is on the screen of the user or in their API response, and what they can do next. |
| **Events**           | A diff for each action of what changed, in the words of the user, not a state dump.                          |
| **Report**           | The outcome numbers of the session and the `note`s of the agent.                                             |
| **Sweep** (optional) | A simple bot policy that plays across many seeds, for numbers and not anecdotes.                             |

Make verbs user-sized: `checkout`, not `POST /payments` then `PATCH /orders`.

The probe is tooling, not product code. It lives next to the tests and links the application as the tests do.

## The contract

Every probe gives these commands, in any language:

| Command                                 | Effect                                                                                                       |
|-----------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `new <session> <boot args...> [seed N]` | Writes the boot line and prints the first view.                                                              |
| `do <session> "<action>" ...`           | Replays the session, runs the actions, and appends the accepted ones. Prints events, a summary and the view. |
| `look <session>`                        | Replays the session and prints the view. Records nothing.                                                    |
| `log <session>`                         | Replays the session and prints every event, action by action.                                                |
| `report <session>`                      | Replays the session and prints the outcome numbers and the notes.                                            |
| `sweep <boot args...> runs N`           | Optional. The bot plays seeds 1 to N and prints the mean, minimum and maximum.                               |

Every probe also has the `note` verb, uses the session file format below, replays on every call, and never records a
refused action.

## The session file

```
boot catalog default seed 7
add mug 2
add shirt 5
note shirt stock message is clear
checkout
```

- Line one is `boot` and the boot arguments. `seed N` at the end seeds everything.
- Each line after it is one accepted action, exactly as typed.
- A **refused** action is never written. A refused action is an unknown verb, or a verb that is invalid in this state
  and spent no time.
- An action that the application **rejected** is written, for example out of stock or payment declined. The rejection is
  behaviour, and the replay must reproduce it.
- If the replay refuses a recorded action, the build changed under the session. Print
  `warning: recorded action refused on replay`, then continue. `check_replay.py` fails on this line.

The probe has no server process and no snapshots. Persistence comes from determinism. Every session is an exact
reproduction that you can attach to a bug.

## Determinism checklist

| Source of nondeterminism | JVM / Spring                                               | Node / TypeScript                           | Python                                    |
|--------------------------|------------------------------------------------------------|---------------------------------------------|-------------------------------------------|
| Wall clock               | inject `java.time.Clock`; `Clock.fixed` or a stepping fake | inject a clock; fake timers in tests        | inject a clock; `time-machine` or a fake  |
| Randomness               | pass a seeded `java.util.Random` / `RandomGenerator`       | seeded generator (e.g. `seedrandom`)        | `random.Random(seed)` per component       |
| Identifiers              | a sequential ID supplier instead of `UUID.randomUUID()`    | sequential ID factory                       | sequential ID factory                     |
| Outside HTTP             | in-process fakes, or WireMock with recorded stubs          | `msw` or in-process fakes                   | in-process fakes, `responses`             |
| Databases                | Testcontainers with a fixed dataset per boot               | Testcontainers or in-memory                 | Testcontainers or SQLite fixture          |
| Concurrency              | run handlers on one thread, or a deterministic executor    | await every promise; no free-running timers | one event loop, no threads                |
| Iteration order          | sorted collections where order reaches the view            | stable sorts                                | sorted dicts where order reaches the view |

## Other languages

Write the probe in the language of the application. The session file format and the commands in the contract are fixed;
the language is not. Do not start the Python kit once for each action of a JVM or Node application. Port the shape of
the kit as the porting reference of this skill describes.

## Writing the view

- Start with a header of one line: where the user is, the time, and the headline numbers.
- Give each item on the screen one labelled line (`CART`, `ERRORS`, `NEXT STEPS`), in the words of the user.
- After each actionable item, put the verb that acts on it in brackets: `[checkout]`. An agent must never guess what it
  can do next.
- Do not show anything that the user cannot see. For debugging, add a separate `inspect` command. Never quote its output
  as evidence of what the user sees.

## Verbs, interrupts and events

- A verb validates its arguments and the current state first. It raises a refusal before it spends time.
- Long verbs (`wait`, `process all`, `run until`) take a hard limit. They stop early on anything that a user reacts to:
  an error, a warning, or a state that the user must answer. The summary says why the verb stopped.
- Events come from a diff of a compact snapshot of user-visible state before and after each step. They do not come from
  logs inside the application. This keeps the probe outside the product code.

## Sweeps

- The bot is a few lines of obvious policy: take the first available action, retry one time, give up. Clever bots hide
  bugs that a simple user hits.
- Report the mean, minimum and maximum of each outcome.
- A sweep number is evidence about the behaviour of the bot, not about real users.

## Maintenance

- When a verb changes, change the verb table in the same commit.
- Remove verbs that nobody used for some time. An agent learns a smaller probe faster.
