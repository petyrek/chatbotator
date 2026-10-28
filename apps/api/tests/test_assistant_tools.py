"""Tests for run_tool: validating the model's arguments and running tools for
the signed-in customer. Plain code, no model involved."""

import json

from chatbotator.assistant.tools import TOOLS, run_tool
from chatbotator.customers import CUSTOMERS

ALEX = CUSTOMERS["customer-alex"]


def test_get_order_returns_the_customers_order() -> None:
    run = run_tool("get_order", {"order_id": "TS-1001"}, ALEX)

    assert not run.is_error
    assert json.loads(run.output) == {
        "order_id": "TS-1001",
        "status": "delivered",
        "ordered_on": "2026-10-08",
        "delivered_on": "2026-10-15",
        "shipping_paid_eur": 5,
        "items": [
            {
                "product": "Alpine 24",
                "quantity": 1,
                "unit_price_eur": 89,
                "condition": "unused",
                "tags_attached": True,
                "standard_return": {"eligible": True, "reasons_not": []},
            }
        ],
        "return_window": {"day": 11, "last_day": "2026-11-14"},
    }


def test_another_customers_order_is_not_found() -> None:
    run = run_tool("get_order", {"order_id": "TS-1003"}, ALEX)  # Sam's order

    assert run.is_error
    assert run.output == "No order TS-1003 found for this customer."


def test_list_orders_shows_only_the_customers_orders() -> None:
    run = run_tool("list_orders", {}, ALEX)

    ids = [order["order_id"] for order in json.loads(run.output)]
    assert "TS-1003" not in ids
    assert len(ids) == 6


def test_the_model_cannot_pass_a_customer() -> None:
    run = run_tool("list_orders", {"customer_id": "customer-sam"}, ALEX)

    assert run.is_error  # unknown arguments are rejected, not ignored
    assert "customer_id" in run.output


def test_invalid_arguments_and_unknown_tools_are_errors_for_the_model() -> None:
    assert run_tool("get_order", {"order_id": "1001"}, ALEX).is_error
    assert run_tool("get_order", {}, ALEX).is_error
    assert run_tool("refund_order", {"order_id": "TS-1001"}, ALEX).is_error


def test_tool_schemas_never_ask_for_a_customer() -> None:
    for tool in TOOLS:
        assert "customer" not in json.dumps(tool["input_schema"])
