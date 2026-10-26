"""Asks the model for the assistant's next reply in a conversation."""

from anthropic import Anthropic
from anthropic.types import MessageParam

MODEL = "claude-haiku-5-5"

SYSTEM_PROMPT = """\
You are the customer support assistant for TrailSupply, a fictional outdoor store.
You help customers with questions about products, shipping, returns and warranty.

You do not have the store's policy documents or any order data yet. If a question
depends on store policy or on a customer's order, say that you can't answer it yet
and suggest contacting support@trailsupply.example.

Never invent policies, prices, dates or order details. Keep answers short and
friendly."""

# One client for the whole app: it keeps a pool of HTTP connections open.
# It reads ANTHROPIC_API_KEY from the environment (loaded from .env at startup).
client = Anthropic()


def generate_reply(messages: list[MessageParam]) -> str:
    """Returns the assistant's reply to the conversation so far.

    `messages` is the full history, oldest first, ending with the user's latest
    message. The API is stateless: it only knows what is sent in this call.
    SDK errors (bad key, rate limit, network) are left for the caller to handle.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=messages,
        # Haiku 5.5 thinks before answering; "low" is enough for short support
        # replies and uses fewer (billed) thinking tokens than the default "medium".
        output_config={"effort": "low"},
    )
    # `content` is a list of blocks. Thinking blocks come first (with empty text
    # by default); the reply itself is in the text blocks.
    return "".join(block.text for block in response.content if block.type == "text")
