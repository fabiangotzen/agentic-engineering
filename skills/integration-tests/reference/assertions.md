# Assertions and waiting

This file describes how to assert results and how to wait for asynchronous effects.

- Use AssertJ (`assertThat`, `assertThatThrownBy`). Do not use JUnit `assertEquals`, `assertTrue`, `assertNull` or `assertThrows`.
- Group related assertions in JUnit `assertAll("what this proves", ...)`. It is the one JUnit assertion that the checker accepts.
- Use a plain `assertThat` for a single assertion.
- Assert on stored state or on the HTTP response. Assert on log output only when the log is the behavior.
- Wait for asynchronous effects with Awaitility and a bounded `atMost`. Never use `Thread.sleep`.
- For a Kafka consumer, publish through the test helper, then wait for the stored state:

```java
// act
testData.publish(new PaymentReceived("order-paid-1"));
// assert
await().atMost(Duration.ofSeconds(10)).untilAsserted(() ->
    assertThat(testData.findOrder("order-paid-1").getStatus()).isEqualTo(OrderStatus.PAID));
```
