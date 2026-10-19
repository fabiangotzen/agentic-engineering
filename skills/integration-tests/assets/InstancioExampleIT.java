package com.example.order;

import static org.assertj.core.api.Assertions.assertThat;
import static org.instancio.Select.field;

import java.time.LocalDate;
import java.util.List;
import org.instancio.Instancio;
import org.instancio.Model;
import org.instancio.junit.InstancioExtension;
import org.instancio.junit.Seed;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;

@DatabaseIntegrationTest
@CleanDbBeforeAll
@ExtendWith(InstancioExtension.class)
class OrderListingIT {

    @Autowired
    OrderService orderService;

    @Autowired
    TestDataService testData;

    @Test
    @Seed(1001)
    @DisplayName("[ORDER] A new order can be cancelled")
    void newOrderCanBeCancelled() {
        // arrange
        testData.save(order("order-cancel-1", OrderStatus.NEW));
        // act
        orderService.cancel("order-cancel-1");
        // assert
        assertThat(testData.findOrder("order-cancel-1").getStatus()).isEqualTo(OrderStatus.CANCELLED);
    }

    @Test
    @Seed(1002)
    @DisplayName("[ORDER] Listing returns all orders of a customer")
    void listingReturnsAllOrdersOfCustomer() {
        // arrange
        List<Order> orders = Instancio.ofList(defaultOrder())
                .size(5)
                .set(field(Order::getCustomerId), "cust-list-1")
                .generate(field(Order::getId), gen -> gen.text().pattern("order-list-#d#d#d"))
                .create();
        orders.forEach(testData::save);
        // act
        var result = orderService.listByCustomer("cust-list-1");
        // assert
        assertThat(result).extracting(Order::getId)
                .containsExactlyInAnyOrderElementsOf(orders.stream().map(Order::getId).toList());
    }

    private static Model<Order> defaultOrder() {
        return Instancio.of(Order.class)
                .generate(field(Order::getQuantity), gen -> gen.ints().range(1, 3))
                .set(field(Order::getStatus), OrderStatus.NEW)
                .set(field(Order::getCreatedOn), LocalDate.of(2024, 5, 15))
                .ignore(field(Order::getVersion))
                .toModel();
    }

    private static Order order(String id, OrderStatus status) {
        return Instancio.of(defaultOrder())
                .set(field(Order::getId), id)
                .set(field(Order::getStatus), status)
                .create();
    }
}
