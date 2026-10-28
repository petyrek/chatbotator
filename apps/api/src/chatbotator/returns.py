"""Whether an order's items can be sent back as a standard return, decided in
code from the order's facts and the rules in data/knowledge/returns.md.

The model never decides this: get_order (assistant/tools.py) includes the result,
and the model reports it. `today` is an argument, so tests can use any date.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from chatbotator.orders import Order

# returns.md, "Return window": the delivery date is day 0; a return requested on
# or before day 30 is in time.
RETURN_WINDOW_DAYS = 30


@dataclass(frozen=True)
class ItemCheck:
    product_name: str
    eligible: bool
    reasons: list[str]  # why not, in the policy's terms; empty when eligible


@dataclass(frozen=True)
class ReturnCheck:
    order_id: str
    delivered: bool
    day: int | None  # days since delivery (delivery day = 0); None if undelivered
    last_day: date | None  # the last day to request a standard return
    items: list[ItemCheck]


def check_return(order: Order, today: date) -> ReturnCheck:
    """Checks each item against the window and the recorded condition.

    Records describe the item as delivered. If the customer says they have used
    it since, it doesn't qualify either; the prompt tells the model so, and the
    store inspects every returned item anyway.
    """
    if order.delivered_on is None:
        reason = "the order hasn't been delivered yet, so it can't be returned"
        items = [ItemCheck(i.product_name, False, [reason]) for i in order.items]
        return ReturnCheck(order.id, False, None, None, items)

    day = (today - order.delivered_on).days
    last_day = order.delivered_on + timedelta(days=RETURN_WINDOW_DAYS)
    items = []
    for item in order.items:
        reasons = []
        if day > RETURN_WINDOW_DAYS:
            reasons.append(f"day {day} is past the {RETURN_WINDOW_DAYS}-day window")
        if item.condition == "used":
            reasons.append("recorded as used")
        if not item.tags_attached:
            reasons.append("original tags not attached")
        items.append(ItemCheck(item.product_name, not reasons, reasons))
    return ReturnCheck(order.id, True, day, last_day, items)
