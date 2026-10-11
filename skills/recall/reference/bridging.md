# Bridging to the stronger language

This file describes how to compare a concept with the language that the user knows better, with a worked table for C++ and Java.

## Method

- Start with the familiar concept in the stronger language. Then show the difference.
- Show where the analogy breaks. At that point, the intuition of the user will mislead them.
- State each guarantee exactly, with its limits. The session grades answers against these comparisons, so an overstated guarantee teaches a wrong rule.
- Do not force a comparison that is not honest. If a concept has no counterpart, say so plainly. "This one has no Java equivalent, which is why it feels alien" is useful for the user to hear.

## Worked table: C++ for a Java developer

| C++ | Java analogue | Where the analogy breaks |
| --- | --- | --- |
| `Order &order` | any object parameter | Java always passes a reference by value. In C++, value, `&` and `*` are a real choice. A missing `&` silently copies the whole object. |
| `const Order &` | `final` parameter | `final` only fixes the variable. `const` also stops calls to non-const member functions and writes to members. It is shallow: data behind a pointer member, `mutable` members and `const_cast` are not protected. |
| `int Order::*` (pointer-to-member) | `java.lang.reflect.Field` | Both name "which field". A pointer-to-member is a typed value that the code can choose at runtime, but the compiler checks its type, and access costs no reflection. |
| templates and concepts | generics and bounded types | C++ templates generate code at compile time, one instantiation for each type. They do not use erasure. A concept is closer to a bounded type parameter than to a plain `<T>`. |
| `std::variant` and `std::visit` | sealed interface and a `switch` pattern match | `std::visit` fails to compile when no overload accepts an alternative. A generic `auto` overload or an implicit conversion accepts the missing case silently, as a `default` branch does in Java. The variant stores its value in place, with no allocation. |
| RAII and destructors | try-with-resources | RAII runs automatically at every scope exit. It is not opt-in for each block, and there is no garbage collector. |
| a raw resource handle | an `int` file handle | Nothing frees it for you. Acquire and release must come in pairs, or an RAII wrapper must own the handle. |
| `struct` with public fields | a record or plain data class | The default access is different: `struct` is public, `class` is private. A `struct` is mutable unless its members are `const`. |

Concepts with no Java counterpart: object lifetime on the stack and on the heap, the split between headers and translation units, and undefined behaviour.
