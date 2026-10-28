"""Asks the model for the assistant's next reply, grounded in the policy documents.

routes/chat.py calls generate_reply() with the conversation; this module adds the
system prompt and the documents, makes the call, and returns the reply with the
policy lines it cites.
"""

import time
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic
from anthropic.types import (
    ContentBlockParam,
    Message,
    MessageParam,
    SearchResultBlockParam,
    UserMessageParam,
)

from chatbotator.assistant.citations import Citation, citations_in
from chatbotator.assistant.prompt import SYSTEM_PROMPT
from chatbotator.policies import DOCUMENTS, Document

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 4096
# How hard the model thinks before answering (thinking is turned on in the
# request below). "low" is enough for short support replies and bills fewer
# thinking tokens.
EFFORT = "low"

# One client for the whole app: it keeps a pool of HTTP connections open.
# It reads ANTHROPIC_API_KEY from the environment, which the npm scripts load
# from the repo-root .env (`--env-file` in package.json).
# The SDK defaults (600 s timeout, 2 retries) suit batch jobs, not a chat where
# someone is waiting: give up after 30 s and retry once (about 60 s at most).
client = Anthropic(timeout=30.0, max_retries=1)


@dataclass(frozen=True)
class ReplyResult:
    """One model call: what was sent, what came back, and how long it took."""

    text: str  # the reply for the customer
    citations: list[Citation]  # the policy lines the reply cites, in order
    request: dict[str, Any]  # exactly the arguments passed to messages.create
    response: Message  # the full API response: content blocks, stop_reason, usage
    latency_s: float

    @property
    def is_complete(self) -> bool:
        """True only if the model finished normally (stop_reason "end_turn") with
        some text. A reply cut off at max_tokens, refused, or empty must not be
        shown as an answer."""
        return self.response.stop_reason == "end_turn" and bool(self.text.strip())


def as_search_results(documents: list[Document]) -> list[SearchResultBlockParam]:
    """The documents in the API's `search_result` format, with citations enabled.

    One text block per passage, so a citation quotes the exact policy line rather
    than the whole document. Each block starts with its section heading, so the
    model reads it in context.
    """
    return [
        {
            "type": "search_result",
            "source": document.name,
            "title": document.title,
            "content": [
                {"type": "text", "text": f"{p.section}: {p.text}"}
                for p in document.passages
            ],
            "citations": {"enabled": True},
        }
        for document in documents
    ]


def with_documents(
    messages: list[MessageParam], documents: list[Document]
) -> list[MessageParam]:
    """Attaches the policy documents to the customer's latest message.

    The API is stateless, so they are attached again on every request. Earlier
    messages are sent unchanged.
    """
    # Unpacks the last message and the ones before it, like
    # `const latest = messages.at(-1); const history = messages.slice(0, -1)`.
    *history, latest = messages
    # Only a plain-text customer message can carry the documents. (A tool loop
    # must attach them before it starts: its later messages are tool results.)
    if not isinstance(latest["content"], str):
        raise TypeError("The latest message must be plain text")
    content: list[ContentBlockParam] = [
        *as_search_results(documents),
        {"type": "text", "text": latest["content"]},
    ]
    with_attachments: UserMessageParam = {"role": "user", "content": content}
    return [*history, with_attachments]


def generate_reply(
    messages: list[MessageParam], documents: list[Document] = DOCUMENTS
) -> ReplyResult:
    """Asks the model for the next reply to the conversation so far.

    `messages` is the full history, oldest first, ending with the user's latest
    message. `documents` are the store's policies; evals can add others, such as
    one with a planted instruction. SDK errors (bad key, rate limit, network) are
    left for the caller.
    """
    # Built once and passed as-is, so what callers log is exactly what was sent.
    # A plain dict rather than a typed one: it is only splatted into create().
    request: dict[str, Any] = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": with_documents(messages, documents),
        # "summarized" makes thinking blocks carry a readable summary (billed the
        # same as hidden thinking), so eval traces show how the model reasoned.
        # Customers only ever get the text blocks.
        "thinking": {"type": "adaptive", "display": "summarized"},
        "output_config": {"effort": EFFORT},
    }
    started = time.perf_counter()
    response = client.messages.create(**request)
    latency_s = time.perf_counter() - started

    # With citations on, the reply arrives as several text blocks (one per cited
    # stretch); joined, they are the reply.
    text = "".join(block.text for block in response.content if block.type == "text")
    return ReplyResult(
        text=text,
        citations=citations_in(response, documents),
        request=request,
        response=response,
        latency_s=latency_s,
    )
