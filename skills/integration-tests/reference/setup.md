# Setup

This file describes how to start containers, connect them to the application, reset state and share test helpers.

- Put containers, profile and framework context in one meta-annotation, for example `@DatabaseIntegrationTest`. A test class then needs one line of setup.
- Give that annotation a `properties` attribute (`@AliasFor`), so that a class can change settings without new boilerplate.
- Start each container once per JVM in a static holder. Never start containers per test class, because container start takes most of the test time.
- Give container URLs and credentials to the application through an `ApplicationContextInitializer` or `@ServiceConnection`. Never hardcode them.
- Reset state with one class-level annotation, for example `@CleanDbBeforeAll`. Do not write cleanup code in each test.
- Put test-only helpers (data lookup, message publisher) in a test `@Service` that a `TestConfig` imports. Tests then stay free of repository code.
- Use real containers, not mocks. Mock only in unit tests of pure domain logic.
- For an external system that has no container (SAP, a partner REST API), stub it with WireMock at the HTTP level.
- When a Mockito mock is the only option, add `// allow-mock: <reason>` on the same line. The checker then accepts it.
- Inject a fixed `Clock` bean in the test configuration. Production code reads time from the `Clock`, never from `now()`.
