# Sources

This file lists the old ideas that a probe combines, and where each idea comes from.

When one of these ideas breaks, its source helps you to find the cause.

## Sessions as action logs

- Martin Fowler, "Event Sourcing" (2005), https://martinfowler.com/eaaDev/EventSourcing.html. State is the result of a
  replay of a log of changes. For the same reason, a probe session holds only a boot line and actions.
- rr, the record-and-replay debugger from Mozilla, https://rr-project.org. It uses deterministic replay as a debugging
  tool, not as a test.

## Deterministic simulation

- Will Wilson, "Testing Distributed Systems w/ Deterministic Simulation", Strange Loop 2014. FoundationDB ran its full
  database inside a deterministic simulator with injected faults.
- The VOPR simulator of TigerBeetle, https://github.com/tigerbeetle/tigerbeetle. It applies the same method to a modern
  financial database, and uses seeds as bug reports.

## Driving systems through their entry points

- Hypothesis stateful testing (`RuleBasedStateMachine`), https://hypothesis.readthedocs.io. It generates sequences of
  user-level actions against a model, and shrinks them to a minimal failing sequence. A sweep bot is a much simpler
  relative.
- Testcontainers, https://testcontainers.com. It gives tests real dependencies. With it, a probe boots a database or a
  broker and does not fake its behaviour.
