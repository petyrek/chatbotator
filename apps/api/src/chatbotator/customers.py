"""Who is signed in.

Only routes call current_customer(). They pass the customer down to the
assistant and its tools as an argument, so the model can never choose whose
data it sees.
"""

import json
from dataclasses import dataclass

from chatbotator.settings import DATA_DIR


@dataclass(frozen=True)
class Customer:
    id: str  # e.g. "customer-alex"; orders refer to it as customerId
    name: str
    email: str


def load_customers() -> dict[str, Customer]:
    """The seeded customers in data/fixtures/customers.json, by id."""
    rows = json.loads((DATA_DIR / "fixtures" / "customers.json").read_text())
    return {row["id"]: Customer(row["id"], row["name"], row["email"]) for row in rows}


CUSTOMERS = load_customers()


def current_customer() -> Customer:
    """The signed-in customer, as a FastAPI dependency (see routes/chat.py).

    A real app reads this from the session cookie or token. This demo has no
    sign-in, so the server always uses Alex. Never take it from the request
    body: anyone could send any id.
    """
    return CUSTOMERS["customer-alex"]
