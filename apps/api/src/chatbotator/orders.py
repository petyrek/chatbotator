"""The store's orders (data/fixtures/orders.json), looked up per customer.

Every lookup takes the customer it is for, so one customer's orders can never be
read on behalf of another. The assistant's tools (assistant/tools.py) call these.
"""

import json
from dataclasses import dataclass
from datetime import date
from typing import Literal

from chatbotator.settings import DATA_DIR

FIXTURES_DIR = DATA_DIR / "fixtures"


@dataclass(frozen=True)
class OrderItem:
    product_id: str  # e.g. "alpine-24"
    product_name: str  # e.g. "Alpine 24", from products.json
    quantity: int
    unit_price: int  # EUR
    condition: Literal["unused", "used"]  # as recorded by the store
    tags_attached: bool


@dataclass(frozen=True)
class Order:
    id: str  # e.g. "TS-1001"
    customer_id: str
    status: Literal["processing", "delivered"]
    ordered_on: date
    delivered_on: date | None  # None until delivered
    shipping_paid: int  # EUR: €5 below €100, €0 at or above
    items: list[OrderItem]


def load_orders() -> list[Order]:
    """Every order in the fixtures, with each item's product name filled in."""
    products = json.loads((FIXTURES_DIR / "products.json").read_text())
    names = {product["id"]: product["name"] for product in products}
    rows = json.loads((FIXTURES_DIR / "orders.json").read_text())["orders"]
    return [
        Order(
            id=row["id"],
            customer_id=row["customerId"],
            status=row["status"],
            ordered_on=date.fromisoformat(row["orderedAt"]),
            delivered_on=(
                date.fromisoformat(row["deliveredAt"]) if row["deliveredAt"] else None
            ),
            shipping_paid=row["shippingPaid"],
            items=[
                OrderItem(
                    product_id=item["productId"],
                    product_name=names[item["productId"]],
                    quantity=item["quantity"],
                    unit_price=item["unitPrice"],
                    condition=item["condition"],
                    tags_attached=item["tagsAttached"],
                )
                for item in row["items"]
            ],
        )
        for row in rows
    ]


ORDERS = load_orders()


def orders_of(customer_id: str) -> list[Order]:
    """The customer's orders, newest first."""
    mine = [order for order in ORDERS if order.customer_id == customer_id]
    return sorted(mine, key=lambda order: order.ordered_on, reverse=True)


def find_order(customer_id: str, order_id: str) -> Order | None:
    """The customer's order with this id, or None.

    Another customer's order is None too, exactly like one that doesn't exist,
    so nobody can find out which order numbers exist by asking for them.
    """
    for order in orders_of(customer_id):
        if order.id == order_id:
            return order
    return None
