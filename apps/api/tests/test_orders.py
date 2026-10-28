"""Tests for looking up orders per customer (the fixtures in data/fixtures/)."""

from datetime import date

from chatbotator.orders import find_order, orders_of


def test_lists_only_the_customers_own_orders_newest_first() -> None:
    ids = [order.id for order in orders_of("customer-alex")]

    assert ids == ["TS-1004", "TS-1001", "TS-1007", "TS-1002", "TS-1005", "TS-1006"]


def test_finds_the_customers_own_order_with_its_items() -> None:
    order = find_order("customer-alex", "TS-1007")

    assert order is not None
    assert order.delivered_on == date(2026, 10, 10)
    assert [(i.product_name, i.condition) for i in order.items] == [
        ("Alpine 24", "unused"),
        ("Roam 750", "used"),
    ]


def test_another_customers_order_is_not_found() -> None:
    assert find_order("customer-sam", "TS-1003") is not None  # it exists...
    assert find_order("customer-alex", "TS-1003") is None  # ...but not for Alex


def test_an_undelivered_order_has_no_delivery_date() -> None:
    order = find_order("customer-alex", "TS-1004")

    assert order is not None
    assert (order.status, order.delivered_on) == ("processing", None)
