"""Asks the model for the assistant's next reply in a conversation."""

import time
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic
from anthropic.types import Message, MessageParam

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 4096
# Haiku 5.5 thinks before answering; "low" is enough for short support replies
# and uses fewer (billed) thinking tokens than the default "medium".
EFFORT = "low"

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


@dataclass(frozen=True)
class ReplyResult:
    """One model call: what was sent, what came back, and how long it took."""

    text: str  # the reply for the customer
    request: dict[str, Any]  # exactly the arguments passed to messages.create
    response: Message  # the full API response: content blocks, stop_reason, usage
    latency_s: float


def generate_reply(messages: list[MessageParam]) -> ReplyResult:
    """Asks the model for the next reply to the conversation so far.

    `messages` is the full history, oldest first, ending with the user's latest
    message. The API is stateless: it only knows what is sent in this call.
    SDK errors (bad key, rate limit, network) are left for the caller to handle.
    """
    # Built once and passed as-is, so what callers log is exactly what was sent.
    request: dict[str, Any] = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": messages,
        # "summarized" makes thinking blocks carry a readable summary (billed the
        # same as hidden thinking), so eval traces show how the model reasoned.
        # Customers only ever get the text blocks.
        "thinking": {"type": "adaptive", "display": "summarized"},
        "output_config": {"effort": EFFORT},
    }
    started = time.perf_counter()
    response = client.messages.create(**request)
    latency_s = time.perf_counter() - started

    # `content` is a list of blocks: thinking first, then the reply as text.
    text = "".join(block.text for block in response.content if block.type == "text")
    return ReplyResult(
        text=text, request=request, response=response, latency_s=latency_s
    )
