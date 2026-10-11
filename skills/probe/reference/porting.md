# Porting the kit

This file describes how to build a probe in the language of the application, with a sketch for Spring Boot.

## Choose the entry point

Drive the application in process, through the entry point that its own tests use. Each call replays the whole session,
so a probe that starts a server or a process for each replay is slow, and it leaks state between replays.

| Application        | In-process entry point                                                       |
|--------------------|------------------------------------------------------------------------------|
| Spring Boot        | `MockMvc` or `WebTestClient` on one application context                      |
| ASP.NET Core       | `WebApplicationFactory` and its `HttpClient`                                 |
| Node / Express     | `supertest` on the app object                                                |
| FastAPI / Django   | `TestClient` / the test `Client`, with `probe_kit.py`                        |
| Game or simulation | the step function, fed with the same input structure as the real input layer |

Use the network only when nothing in-process exists. Then the Python kit is a fine choice.

## What to port

Port the shape of `probe_kit.py`, not its lines. A port has these parts:

1. A `Harness` with `boot(args, seed)`, `view()`, and optional `botAction()` and `outcome()`.
2. A verb registry: a name, a usage text, and a function that returns a summary or raises `Refused`.
3. The CLI commands in the contract, with a replay of the session file at the start of each call.
4. A replay that resets every piece of state: the database, the fakes, the clock and the generators. Reuse one expensive
   object, such as an application context, only when a reset returns it to the boot state.
5. Events from a diff of a compact snapshot of user-visible state before and after each action.
6. `note`, and refusals that are never written to the session file.

Then run `check_replay.py <session file> -- <probe command...>`, and add the same check to the test suite of the
project.

## Sketch: Spring Boot

```java
class ShopProbe extends Harness {
    static final ConfigurableApplicationContext ctx = new SpringApplicationBuilder(ShopApplication.class)
            .profiles("probe").web(WebApplicationType.SERVLET).run();
    final MockMvc http = MockMvcBuilders.webAppContextSetup((WebApplicationContext) ctx)
            .apply(springSecurity()).build();
    final ProbeClock clock = ctx.getBean(ProbeClock.class);
    final ProbeReset reset = ctx.getBean(ProbeReset.class); // truncates tables, reloads the fixture, reseeds the fakes

    void boot(List<String> args, long seed) {
        reset.to(args.get(0), seed);
    }

    @Verb(name = "add", usage = "sku qty")
    String add(List<String> a) throws Exception {
        var r = http.perform(post("/cart/items").contentType(JSON)
                .content("{\"sku\":\"%s\",\"qty\":%s}".formatted(a.get(0), a.get(1)))).andReturn();
        return r.getResponse().getStatus() == 201 ? "added" : "rejected: " + r.getResponse().getContentAsString();
    }

    @Verb(name = "wait", usage = "minutes")
    String waitFor(List<String> a) {
        clock.advance(Duration.ofMinutes(Long.parseLong(a.get(0))));
        return "waited";
    }

    String view() throws Exception {
        return "CART " + http.perform(get("/cart")).andReturn().getResponse().getContentAsString();
    }
}
```

The context starts one time for each CLI call. `boot` calls `reset.to`, so each replay starts from the boot state. Run
the probe without a web port, for example with `server.port=-1` in the probe profile. Run `@Async` and `@Scheduled` work
on a synchronous executor, or expose it as a verb such as `tick 10m`.
