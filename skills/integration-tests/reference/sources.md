# Sources

This file lists where the rules of this skill come from, so that you can judge if a rule fits a project.

- Bill Wake, "3A: Arrange, Act, Assert" (2001), https://xp123.com/3a-arrange-act-assert/. The source of the three phase comments.
- Nat Pryce, "Test Data Builders", in Freeman and Pryce, "Growing Object-Oriented Software, Guided by Tests" (2009). The source of the default builder with overrides.
- Testcontainers, "Singleton containers", https://java.testcontainers.org/test_framework_integration/manual_lifecycle_control/. The source of one container start per JVM.
- Spring Boot, "Testcontainers" and `@ServiceConnection`, https://docs.spring.io/spring-boot/reference/testing/testcontainers.html.
- Awaitility, https://github.com/awaitility/awaitility. Bounded waits for asynchronous effects instead of `Thread.sleep`.
- Mutation testing, for example PIT, https://pitest.org. The idea behind "break the code once and confirm that the test fails".
