package com.example.order;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.awaitility.Awaitility.await;
import static org.junit.jupiter.api.Assertions.assertAll;

import java.time.Duration;
import java.time.LocalDate;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;

@DatabaseIntegrationTest(properties = "app.orders.max-quantity=3")
@CleanDbBeforeAll
class OrderServiceIT {

    @Autowired
    OrderService orderService;

    @Autowired
    TestDataService testData;

    @Test
    @DisplayName("[ORDER] A placed order is stored with status NEW")
    void placedOrderIsStoredAsNew() {
        // arrange
        var customer = testData.save(customer("cust-place-1"));
        // act
        var order = orderService.place(customer.getId(), "sku-1", 2);
        // assert
        var stored = testData.findOrder(order.getId());
        assertAll("stored order",
                () -> assertThat(stored.getStatus()).isEqualTo(OrderStatus.NEW),
                () -> assertThat(stored.getQuantity()).isEqualTo(2),
                () -> assertThat(stored.getCreatedOn()).isEqualTo(LocalDate.of(2024, 5, 15)));
    }

    @ParameterizedTest
    @ValueSource(ints = {0, 4})
    @DisplayName("[ORDER] An order with a quantity outside the limits is rejected")
    void quantityOutsideLimitsIsRejected(int quantity) {
        // arrange
        var customer = testData.save(customer("cust-limit-" + quantity));
        // act + assert
        assertThatThrownBy(() -> orderService.place(customer.getId(), "sku-1", quantity))
                .isInstanceOf(InvalidOrderException.class);
    }

    @Test
    @DisplayName("[ORDER] A received payment marks the order as paid")
    void receivedPaymentMarksOrderAsPaid() {
        // arrange
        testData.save(order("order-paid-1", OrderStatus.NEW));
        // act
        testData.publish(new PaymentReceived("order-paid-1"));
        // assert
        await().atMost(Duration.ofSeconds(10)).untilAsserted(() ->
                assertThat(testData.findOrder("order-paid-1").getStatus()).isEqualTo(OrderStatus.PAID));
    }

    private static Customer customer(String id) {
        return CustomerBuilder.defaultCustomerBuilder().id(id).build();
    }

    private static Order order(String id, OrderStatus status) {
        return OrderBuilder.defaultOrderBuilder().id(id).status(status).build();
    }
}
