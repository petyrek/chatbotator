"""Tests for check_return against every fixture order (data/fixtures/README.md
says what each one is for). "Today" is the fixtures' date, 26 October 2026."""

from datetime import date

import pytest

from chatbotator.orders import ORDERS
from chatbotator.returns import ReturnCheck, check_return

TODAY = date(2026, 10, 26)


def check(order_id: str) -> ReturnCheck:
    order = next(order for order in ORDERS if order.id == order_id)
    return check_return(order, TODAY)


@pytest.mark.parametrize(
    ("order_id", "day", "last_day"),
    [
        ("TS-1001", 11, date(2026, 11, 14)),  # recent, unused, tags attached
        ("TS-1003", 6, date(2026, 11, 19)),  # Sam's order: same rules
        ("TS-1005", 30, date(2026, 10, 26)),  # day 30: the last day, still in time
    ],
)
def test_unused_items_with_tags_inside_the_window_are_eligible(
    order_id: str, day: int, last_day: date
) -> None:
    result = check(order_id)

    assert (result.day, result.last_day) == (day, last_day)
    assert all(item.eligible and not item.reasons for item in result.items)


def test_day_31_is_too_late() -> None:
    [item] = check("TS-1006").items

    assert not item.eligible
    assert item.reasons == ["day 31 is past the 30-day window"]


def test_a_used_item_without_tags_is_not_eligible_even_in_the_window() -> None:
    result = check("TS-1002")

    assert result.day == 21
    assert result.items[0].reasons == ["recorded as used", "original tags not attached"]


def test_each_item_is_assessed_on_its_own() -> None:
    backpack, bottle = check("TS-1007").items

    assert (backpack.product_name, backpack.eligible) == ("Alpine 24", True)
    assert (bottle.product_name, bottle.eligible) == ("Roam 750", False)


def test_an_undelivered_order_cannot_be_returned() -> None:
    result = check("TS-1004")

    assert (result.delivered, result.day, result.last_day) == (False, None, None)
    assert not result.items[0].eligible
