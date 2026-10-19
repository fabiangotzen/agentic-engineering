# Assertions and waiting

This file describes how to assert results and how to wait for asynchronous effects.

- Use AssertJ (`assertThat`, `assertThatThrownBy`). Do not use JUnit `assertEquals`, `assertTrue`, `assertNull` or `assertThrows`.
- Group related assertions in JUnit `assertAll("what this proves", ...)`. It is the one JUnit assertion that the checker accepts.
- Use a plain `assertThat` for a single assertion.
- Assert on stored state or on the HTTP response. Assert on log output only when the log is the behavior.
- Assert lists in any order (`containsExactlyInAnyOrder`), because a query without `ORDER BY` has no fixed order.
- Use `containsExactly` only when the query has `ORDER BY`, and add `// allow-order: <reason>` on that line.
- Do not assert on ids or timestamps that the database generates. Sequence values depend on the tests that ran before.
- Wait for asynchronous effects with Awaitility and a bounded `atMost`. Never use `Thread.sleep`.
- To prove that nothing happens, wait for a fixed time with `during`, because a plain `await` passes at once:

```java
await().during(Duration.ofSeconds(2)).atMost(Duration.ofSeconds(3)).untilAsserted(() ->
    assertThat(testData.findOrder("order-dup-1").getPayments()).hasSize(1));
```

- For a Kafka consumer, publish through the test helper, then wait for the stored state:

```java
// act
testData.publish(new PaymentReceived("order-paid-1"));
// assert
await().atMost(Duration.ofSeconds(10)).untilAsserted(() ->
    assertThat(testData.findOrder("order-paid-1").getStatus()).isEqualTo(OrderStatus.PAID));
```
