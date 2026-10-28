"""The tools the model can call, and running them for the signed-in customer.

The model only asks for a tool; this code decides what happens. reply.py sends
TOOLS with every request and calls run_tool() for each tool call in a response.
- Arguments are validated with Pydantic before anything runs.
- The customer always comes from the server, never from the model's arguments.
- Failures go back to the model as error results, so it can recover or explain,
  instead of crashing the conversation.
"""

import json
from dataclasses import dataclass
from typing import Any

from anthropic.types import ToolParam
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from chatbotator.customers import Customer
from chatbotator.orders import Order, find_order, orders_of
from chatbotator.returns import check_return
from chatbotator.settings import TODAY


class ListOrdersInput(BaseModel):
    # Reject arguments the schema doesn't define, instead of ignoring them.
    model_config = ConfigDict(extra="forbid")


class GetOrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(
        pattern=r"^TS-\d{4}$", description="The order number, e.g. TS-1001."
    )


# What the model sees: each tool's name, when to use it, and its arguments as a
# JSON schema (generated from the Pydantic models above, so they can't drift).
TOOLS: list[ToolParam] = [
    {
        "name": "list_orders",
        "description": (
            "Lists the signed-in customer's orders, newest first: order number, "
            "status, dates and product names. Use it when the customer refers to "
            "an order without its number."
        ),
        "input_schema": ListOrdersInput.model_json_schema(),
    },
    {
        "name": "get_order",
        "description": (
            "Gets one of the signed-in customer's orders by its number: status, "
            "dates, shipping paid, each item's price, condition and tags, and "
            "whether each item can be sent back as a standard return (decided "
            "by the store's rules, with the reasons if not)."
        ),
        "input_schema": GetOrderInput.model_json_schema(),
    },
]


@dataclass(frozen=True)
class ToolRun:
    """One tool call the model made, and what we sent back as its result."""

    name: str
    arguments: Any  # as the model sent them, before validation
    output: str  # the tool_result content: JSON on success, a sentence on error
    is_error: bool


def run_tool(name: str, arguments: Any, customer: Customer) -> ToolRun:
    """Runs one tool call for `customer` and returns its result for the model."""

    def ok(result: Any) -> ToolRun:
        return ToolRun(name, arguments, json.dumps(result), is_error=False)

    def error(message: str) -> ToolRun:
        return ToolRun(name, arguments, message, is_error=True)

    try:
        match name:  # like a switch on the tool name
            case "list_orders":
                ListOrdersInput.model_validate(arguments)
                return ok([summary(order) for order in orders_of(customer.id)])
            case "get_order":
                order_id = GetOrderInput.model_validate(arguments).order_id
                order = find_order(customer.id, order_id)
                if order is None:
                    return error(f"No order {order_id} found for this customer.")
                return ok(details(order))
            case _:
                return error(f"Unknown tool: {name}")
    except ValidationError as invalid:
        return error(f"Invalid arguments: {invalid.errors(include_url=False)}")


# Only the fields the model needs: no email or address ever reaches it.


def dates(order: Order) -> dict[str, Any]:
    delivered = order.delivered_on.isoformat() if order.delivered_on else None
    return {"ordered_on": order.ordered_on.isoformat(), "delivered_on": delivered}


def summary(order: Order) -> dict[str, Any]:
    return {
        "order_id": order.id,
        "status": order.status,
        **dates(order),
        "products": [item.product_name for item in order.items],
    }


def details(order: Order) -> dict[str, Any]:
    returns = check_return(order, TODAY)
    return {
        "order_id": order.id,
        "status": order.status,
        **dates(order),
        "shipping_paid_eur": order.shipping_paid,
        "items": [
            {
                "product": item.product_name,
                "quantity": item.quantity,
                "unit_price_eur": item.unit_price,
                "condition": item.condition,
                "tags_attached": item.tags_attached,
                "standard_return": {
                    "eligible": verdict.eligible,
                    "reasons_not": verdict.reasons,
                },
            }
            # zip pairs each item with its eligibility (same order, same length).
            for item, verdict in zip(order.items, returns.items, strict=True)
        ],
        "return_window": {
            "day": returns.day,  # days since delivery; delivery day = 0
            "last_day": returns.last_day.isoformat() if returns.last_day else None,
        },
    }
