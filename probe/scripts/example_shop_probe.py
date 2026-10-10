#!/usr/bin/env python3
"""Worked example: a probe for a small shop service, driven only through its public API.

    python example_shop_probe.py new s.probe catalog default seed 7
    python example_shop_probe.py do s.probe "add mug 2" "checkout"
    python example_shop_probe.py sweep catalog default runs 50

The Shop class stands in for your real application: in a real probe you would import it, or call its
HTTP API, and wire its clock, randomness and payment gateway to the deterministic fakes below.

Requires Python 3 and no other packages. Keep probe_kit.py in the same directory.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from probe_kit import Harness, Refused, main, verb

# Minutes a cart may sit idle before the shop empties it.
CART_TTL_MINUTES = 30
# Share of payments the fake gateway declines.
DECLINE_RATE = 0.1
# Prime that offsets the payment generator's seed, so payments and the bot draw different random numbers.
PAYMENT_SEED_OFFSET = 7919
# Minutes that one add and one checkout take on the fake clock.
ADD_MINUTES = 1
CHECKOUT_MINUTES = 2
# The sweep bot stops after this many orders or after this many minutes.
BOT_MAX_ORDERS = 3
BOT_MAX_MINUTES = 120
# Chance that the bot checks out a full cart instead of waiting.
BOT_CHECKOUT_CHANCE = 0.7
# Range of minutes the bot waits, and range of the quantity it adds.
BOT_WAIT_MINUTES = (5, 40)
BOT_QUANTITY = (1, 3)


class FakeClock:
    def __init__(self) -> None:
        self.minutes = 0

    def now(self) -> int:
        return self.minutes


class FakePaymentGateway:
    """Behaves like the real gateway, including declines, but decides with a seeded generator."""

    def __init__(self, rng: random.Random, decline_rate: float = DECLINE_RATE) -> None:
        self.rng = rng
        self.decline_rate = decline_rate

    def charge(self, cents: int) -> bool:
        return self.rng.random() >= self.decline_rate


@dataclass
class Shop:
    clock: FakeClock
    payments: FakePaymentGateway
    prices: dict[str, int]
    stock: dict[str, int]
    cart: dict[str, int] = field(default_factory=dict)
    cart_touched: int = 0
    orders: list[int] = field(default_factory=list)

    def add_to_cart(self, sku: str, quantity: int) -> None:
        self.expire_cart_if_stale()
        if sku not in self.prices:
            raise ValueError(f"no such product: {sku}")
        if self.stock[sku] < self.cart.get(sku, 0) + quantity:
            raise ValueError(f"only {self.stock[sku]} {sku} left")
        self.cart[sku] = self.cart.get(sku, 0) + quantity
        self.cart_touched = self.clock.now()

    def expire_cart_if_stale(self) -> bool:
        if self.cart and self.clock.now() - self.cart_touched > CART_TTL_MINUTES:
            self.cart.clear()
            return True
        return False

    def total(self) -> int:
        return sum(self.prices[sku] * quantity for sku, quantity in self.cart.items())

    def checkout(self) -> str:
        if self.expire_cart_if_stale():
            return "expired"
        if not self.cart:
            raise ValueError("cart is empty")
        if not self.payments.charge(self.total()):
            return "declined"
        for sku, quantity in self.cart.items():
            self.stock[sku] -= quantity
        self.orders.append(self.total())
        self.cart.clear()
        return "paid"


# Demo catalogs: product prices in cents and stock levels. "scarce" makes stock limits easy to hit.
CATALOGS = {
    "default": ({"mug": 1200, "shirt": 2500, "poster": 900}, {"mug": 5, "shirt": 2, "poster": 10}),
    "scarce": ({"mug": 1200, "shirt": 2500}, {"mug": 1, "shirt": 1}),
}


def euros(cents: int) -> str:
    return f"€{cents / 100:.2f}"


class ShopProbe(Harness):
    def boot(self, args: list[str], seed: int) -> None:
        name = args[1] if len(args) >= 2 and args[0] == "catalog" else "default"
        if name not in CATALOGS:
            raise SystemExit(f"error: unknown catalog '{name}'. Catalogs: {', '.join(sorted(CATALOGS))}")
        prices, stock = CATALOGS[name]
        self.rng = random.Random(seed)
        self.shop = Shop(FakeClock(), FakePaymentGateway(random.Random(seed * PAYMENT_SEED_OFFSET)), dict(prices), dict(stock))
        self.declines = self.expired = self.refusals = 0
        self.emit(f"booted catalog '{name}' with seed {seed}")

    def view(self) -> str:
        shop = self.shop
        lines = [f"== minute {shop.clock.now()} | orders {len(shop.orders)}"]
        lines.append("PRODUCTS " + ", ".join(f"{sku} {euros(price)} ({shop.stock[sku]} left)" for sku, price in shop.prices.items()))
        if shop.cart:
            idle = shop.clock.now() - shop.cart_touched
            lines.append("CART " + ", ".join(f"{qty}x {sku}" for sku, qty in shop.cart.items())
                         + f" | total {euros(shop.total())} | expires in {max(0, CART_TTL_MINUTES - idle)} min [checkout]")
        else:
            lines.append("CART empty [add <sku> <qty>]")
        return "\n".join(lines)

    @verb("add", "<sku> [qty]")
    def add(self, args: list[str]) -> str:
        if not args:
            raise Refused("add needs a product")
        try:
            quantity = int(args[1]) if len(args) > 1 else 1
        except ValueError:
            raise Refused(f"quantity must be a whole number, got '{args[1]}'")
        try:
            self.shop.add_to_cart(args[0], quantity)
        except ValueError as error:
            self.refusals += 1
            self.emit(f"shop said: {error}")
            return "not added"
        self.shop.clock.minutes += ADD_MINUTES
        return f"added {quantity}x {args[0]}"

    @verb("checkout")
    def checkout(self, args: list[str]) -> str:
        try:
            result = self.shop.checkout()
        except ValueError as error:
            raise Refused(str(error))
        self.shop.clock.minutes += CHECKOUT_MINUTES
        if result == "declined":
            self.declines += 1
            self.emit("payment declined; cart kept")
        elif result == "expired":
            self.expired += 1
            self.emit(f"cart expired after {CART_TTL_MINUTES} idle minutes")
        else:
            self.emit(f"order placed for {euros(self.shop.orders[-1])}")
        return result

    @verb("wait", "<minutes>")
    def wait(self, args: list[str]) -> str:
        try:
            self.shop.clock.minutes += int(args[0]) if args else 1
        except ValueError:
            raise Refused(f"minutes must be a whole number, got '{args[0]}'")
        return f"waited until minute {self.shop.clock.now()}"

    def bot_action(self) -> str | None:
        if len(self.shop.orders) >= BOT_MAX_ORDERS or self.shop.clock.now() > BOT_MAX_MINUTES:
            return None
        if self.shop.cart:
            return "checkout" if self.rng.random() < BOT_CHECKOUT_CHANCE else f"wait {self.rng.randint(*BOT_WAIT_MINUTES)}"
        in_stock = [sku for sku, left in self.shop.stock.items() if left > 0]
        if not in_stock:
            return None
        return f"add {self.rng.choice(in_stock)} {self.rng.randint(*BOT_QUANTITY)}"

    def outcome(self) -> dict[str, float]:
        return {
            "orders": len(self.shop.orders),
            "revenue_eur": sum(self.shop.orders) / 100,
            "declines": self.declines,
            "expired_carts": self.expired,
            "refused_adds": self.refusals,
            "minutes": self.shop.clock.now(),
        }


if __name__ == "__main__":
    raise SystemExit(main(ShopProbe))
