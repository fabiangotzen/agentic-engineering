# Setup

This file describes how to start containers, connect them to the application, reset state and share test helpers.

- Put containers, profile and framework context in one meta-annotation, for example `@DatabaseIntegrationTest`. A test class then needs one line of setup.
- Give that annotation a `properties` attribute (`@AliasFor`), so that a class can change settings without new boilerplate.
- Use that attribute rarely. Each different value starts a new application context, and old contexts stay alive with their Kafka listeners.
- Start each container once per JVM in a static holder. Never start containers per test class, because container start takes most of the test time.
- Pin the full image version, for example `postgres:16.4-alpine`, never `postgres:16` or `latest`.
- Give container URLs and credentials to the application through an `ApplicationContextInitializer` or `@ServiceConnection`. Never hardcode them.
- Reset state with one class-level annotation, for example `@CleanDbBeforeAll`. Do not write cleanup code in each test.
- Class-level cleanup means that tests in a class share data. Every test must use its own ids and must not read data of another test.
- When a test reads global state (a count, "find all"), clean before each test, for example with `@CleanDbBeforeEach`.
- When tests run in parallel against one database, unique ids per test are required, not optional.
- Put test-only helpers (data lookup, message publisher) in a test `@Service` that a `TestConfig` imports. Tests then stay free of repository code.
- Use real containers, not mocks. Mock only in unit tests of pure domain logic.
- For an external system that has no container, stub it with WireMock at the HTTP level.
- When a Mockito mock is the only option, add `// allow-mock: <reason>` on the same line. The checker then accepts it.
- Inject a fixed `Clock` bean in the test configuration. Production code reads time from the `Clock`, never from `now()`.
- Time that the database sets (`DEFAULT now()`, `CURRENT_TIMESTAMP`, `@CreationTimestamp`, JPA auditing) ignores the `Clock`. Do not assert on it, or give auditing a `DateTimeProvider` that reads the `Clock`.

## Kafka

- Give each application context its own consumer group, so that a cached context does not take the messages of another context.
- Use a unique message key or topic per test, because messages and offsets stay on the broker between test classes.
- Wait until the listener containers have their partitions before the first test publishes, for example with `ContainerTestUtils.waitForAssignment`.
