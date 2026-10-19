---
name: integration-tests
description: Writes, reviews and refactors integration tests that run the real application against Testcontainers (database, Kafka and others), with an opinionated Spring Boot setup and a convention checker for Java and Kotlin. Use when the user adds or fixes an integration test, an `*IT` class, a Testcontainers setup, a test data builder or test annotations, even if they only say "add a test for this service" or "test this consumer".
---

# Integration tests

## Purpose

Integration tests run the real application against real containers.
They catch wiring and persistence bugs that mocks hide.

## Workflow

```
- [ ] 1. Read the project rules
- [ ] 2. Reuse or create the setup
- [ ] 3. Build the test data
- [ ] 4. Write the tests
- [ ] 5. Run the checker
- [ ] 6. Run the tests and break the code once
```

1. Read the closest existing `*IT` class and the project test guide, for example `docs/TESTING.md`. Project rules win over this skill.
2. Reuse the setup annotation of the project. Create one only if none exists.
3. Build the test data with builders and fixed values.
4. Write the tests with the rules below.
5. Run the checker on the changed test files and fix every finding.
6. Run the tests with the project command. Break the production behavior once, confirm that the test fails, then revert the break.

## Test structure

- Mark the phases with `// arrange`, `// act` and `// assert`, in this order.
- Use `// act + assert` only when the assertion wraps the action, for example `assertThatThrownBy`.
- Keep exactly one action under `// act`, so that a failure points to one cause.
- Add `@DisplayName("[AREA] expected behavior")` to every test. `AREA` is the bounded context or top-level package, in capitals.
- Write the display name as one sentence that a business person can read.
- Name the method after the behavior that it proves, not after the method that it calls.
- Use `@ParameterizedTest` when only the input changes between cases.
- End the class name with `IT`, so that the build runs it as an integration test.

## Reference files

- Before you create or change the setup (containers, annotations, cleanup, helpers), read [reference/setup.md](reference/setup.md).
- Before you write test data, read [reference/test-data.md](reference/test-data.md).
- Before you write assertions or wait for async effects (Kafka, events), read [reference/assertions.md](reference/assertions.md).
- When the project uses Spring Boot, read [reference/spring-boot.md](reference/spring-boot.md) and copy [assets/ExampleIT.java](assets/ExampleIT.java) as the start point.
- When the project uses .NET, Python, Node or Go, read [reference/other-frameworks.md](reference/other-frameworks.md).
- When a rule seems wrong for the project, read [reference/sources.md](reference/sources.md) for the reason behind it.

## Scripts

The script needs Python 3 and no other packages.

- RUN `python <this skill's folder>/scripts/check_test_conventions.py <test files>` on Java and Kotlin test files.
  It prints `file:line: [rule] message` for each finding and exits with 0 when clean, 1 on findings and 2 on a usage error.
- The checker passes on `assets/ExampleIT.java`. Run it on that file after you change the checker.
