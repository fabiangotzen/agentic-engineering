# Spring Boot setup

This file gives the Spring Boot skeleton for the rules in the setup reference: meta-annotation, container holder, cleanup and test helpers.

## Meta-annotation

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@SpringBootTest
@ActiveProfiles("it")
@ContextConfiguration(initializers = Containers.Initializer.class)
@Import(TestConfig.class)
public @interface DatabaseIntegrationTest {
    @AliasFor(annotation = SpringBootTest.class, attribute = "properties")
    String[] properties() default {};
}
```

## Containers, once per JVM

```java
public final class Containers {
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");
    static final KafkaContainer KAFKA = new KafkaContainer("apache/kafka:3.8.0");

    static {
        Startables.deepStart(POSTGRES, KAFKA).join();
    }

    public static class Initializer implements ApplicationContextInitializer<ConfigurableApplicationContext> {
        @Override
        public void initialize(ConfigurableApplicationContext context) {
            TestPropertyValues.of(
                    "spring.datasource.url=" + POSTGRES.getJdbcUrl(),
                    "spring.datasource.username=" + POSTGRES.getUsername(),
                    "spring.datasource.password=" + POSTGRES.getPassword(),
                    "spring.kafka.bootstrap-servers=" + KAFKA.getBootstrapServers())
                .applyTo(context);
        }
    }
}
```

With Spring Boot 3.1 or later, `@ServiceConnection` on static container beans in a `@TestConfiguration` can replace the initializer.

## Cleanup

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Sql(scripts = "classpath:sql/clean.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_CLASS)
public @interface CleanDbBeforeAll {}
```

`BEFORE_TEST_CLASS` needs Spring Framework 6.1 or later.

## Test helpers and clock

```java
@TestConfiguration
@Import(TestDataService.class)
public class TestConfig {
    @Bean
    @Primary
    Clock fixedClock() {
        return Clock.fixed(Instant.parse("2024-05-15T10:00:00Z"), ZoneOffset.UTC);
    }
}

@Service
public class TestDataService {
    private final OrderRepository orders;
    private final KafkaTemplate<String, Object> kafka;

    public TestDataService(OrderRepository orders, KafkaTemplate<String, Object> kafka) {
        this.orders = orders;
        this.kafka = kafka;
    }

    public Order save(Order order) { return orders.save(order); }
    public Order findOrder(String id) { return orders.findById(id).orElseThrow(); }
    public void publish(Object event) { kafka.send("payments", event).join(); }
}
```

## Build

- Gradle: name the classes `*IT` and run them in a separate `integrationTest` task or test suite.
- Maven: the Failsafe plugin runs `*IT` classes in the `integration-test` phase.
