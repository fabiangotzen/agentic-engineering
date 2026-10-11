# Bridging to the stronger language

This file describes how to compare a concept with the language that the user knows better, with a worked table for C++ and Java.

## Method

- Start with the familiar concept in the stronger language. Then show the difference.
- Show where the analogy breaks. At that point, the intuition of the user will mislead them.
- Do not force a comparison that is not honest. If a concept has no counterpart, say so plainly. "This one has no Java equivalent, which is why it feels alien" is useful for the user to hear.

## Worked table: C++ for a Java developer

| C++ | Java analogue | Where the analogy breaks |
| --- | --- | --- |
| `GameState &state` | any object parameter | Java always passes a reference by value. In C++, `&`, value and `*` are a real choice. A missing `&` silently copies the whole object. |
| `const GameState &` | no equivalent | Java has no deep immutability that the compiler enforces. `final` only fixes the variable. `const` here is a real guarantee. |
| `float CooldownState::*` | `java.lang.reflect.Field` | The idea of "which field" is the same. C++ resolves it at compile time, with no reflection cost. |
| templates and concepts | generics and bounded types | C++ templates generate code at compile time, one class for each type. They do not use erasure. A concept is closer to a Java interface bound than to `<T>`. |
| `std::variant` and `std::visit` | sealed interface and a `switch` pattern match | Both make a missing case a compile error. The C++ version stores the value in place, with no allocation. |
| RAII and destructors | try-with-resources | RAII runs automatically at every scope exit. It is not opt-in for each block, and there is no garbage collector. |
| a raw resource handle | an `int` file handle | Nothing frees it for you. Load and unload functions must come in pairs. |
| `struct` with public fields | a record or plain data class | The default access is different: `struct` is public, `class` is private. |

Concepts with no Java counterpart: object lifetime on the stack and on the heap, the split between headers and translation units, and undefined behaviour.
