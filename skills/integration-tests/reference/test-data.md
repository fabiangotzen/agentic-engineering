# Test data

This file describes how to build test data that keeps the intent of a test visible and makes a failure reproducible.

- Build data with a builder that has a `default...Builder()` factory. Change only the fields that the test is about.
- Wrap builder calls in private helper methods that show only the parameters that matter for the test.
- Use fixed literals for ids, names and dates, for example `LocalDate.of(2024, 5, 15)`.
- Make each id unique per test with a fixed prefix from the test name, for example `"order-cancel-1"`. Tests then do not collide in a shared database.
- Do not use `Random`, `UUID.randomUUID()`, `Faker` or `now()`.
- When you need many unique values, use a name-based generator, for example `UUID.nameUUIDFromBytes("order-cancel-1".getBytes())`.
- Keep builders in the test source set. Share them across modules with Gradle `java-test-fixtures` or a Maven `test-jar`.

## Generated data with Instancio

- Use Instancio when a test needs full objects but cares about only a few fields.
- Keep the fields with business meaning in a shared `Model`, and let Instancio fill the rest.
- Give every test that uses Instancio its own seed with `@Seed(<number>)`, so that each test is reproducible and other tests do not change its data.
- Use a different seed in each test of a class. The checker flags a missing or repeated seed.
- Set ids yourself with a per-test prefix, because the same seed in two classes gives the same values.
- Use `ignore(...)` for fields that the database or the framework manages, for example `version`.
- Add `@ExtendWith(InstancioExtension.class)` to the class, so that `@Seed` takes effect and the seed shows in a failure.
