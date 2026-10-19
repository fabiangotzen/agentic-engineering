# Other frameworks

This file maps the rules of this skill to .NET, Python, Node and Go. The checker covers only Java and Kotlin.

| Rule                     | .NET                               | Python                              | Node                                 | Go                                  |
|--------------------------|------------------------------------|-------------------------------------|--------------------------------------|-------------------------------------|
| Containers once per run  | `ICollectionFixture` + Testcontainers for .NET | session-scoped pytest fixture + `testcontainers` | Jest or Vitest `globalSetup` + `@testcontainers/*` | `TestMain` + `testcontainers-go` |
| App against containers   | `WebApplicationFactory`            | app factory with fixture settings   | app started in `globalSetup`         | `httptest.Server` with real config  |
| Readable test name       | `[Fact(DisplayName = "...")]`      | test name or `pytest.mark` id       | `it("...")`                          | `t.Run("...")`                      |
| Fluent assertions        | Shouldly or AwesomeAssertions      | plain `assert`                      | `expect`                             | `testify/assert`                    |
| Bounded wait             | `Polly` retry with timeout         | `tenacity` with `stop_after_delay`  | `vi.waitFor` or `waitFor`            | `assert.Eventually`                 |
| Fixed time               | `TimeProvider` + `FakeTimeProvider` | `freezegun` or an injected clock   | `vi.useFakeTimers` + `setSystemTime` | injected `func() time.Time`         |

Check the same patterns by hand with grep:

```
grep -rnE "sleep\(|Thread\.Sleep|time\.Sleep|setTimeout|random|uuid4|Guid\.NewGuid|uuid\.New\(|Faker|now\(\)|Now\b" <test folder>
```
