"""Asks the model for the assistant's next reply: a bounded loop of model calls
and tool calls.

routes/chat.py calls generate_reply() with the conversation and the signed-in
customer. Each step sends the conversation to the model. If the model asks for
tools (stop_reason "tool_use"), we run them (tools.py), add the results to the
conversation and call it again. The loop ends when the model answers, after
MAX_STEPS calls, or when the turn's time runs out.
"""

import time
from dataclasses import dataclass
from typing import Any, cast

from anthropic import Anthropic
from anthropic.types import (
    ContentBlockParam,
    Message,
    MessageParam,
    SearchResultBlockParam,
    ToolResultBlockParam,
    UserMessageParam,
)

from chatbotator.assistant.citations import Citation, citations_in
from chatbotator.assistant.prompt import SYSTEM_PROMPT
from chatbotator.assistant.tools import TOOLS, ToolRun, run_tool
from chatbotator.customers import Customer
from chatbotator.policies import DOCUMENTS, Document

MODEL = "claude-haiku-5-5"
MAX_TOKENS = 4096
# How hard the model thinks before answering (thinking is turned on in the
# request below). "low" is enough for short support replies and bills fewer
# thinking tokens.
EFFORT = "low"

# A turn is one customer message and everything until the reply. It may take
# several model calls: one per step, plus one tool round between steps.
MAX_STEPS = 5  # a loop that hasn't answered by then is stuck
TURN_DEADLINE_S = 60.0  # the browser stops waiting at 65 s (CHAT_TIMEOUT_MS)
CALL_TIMEOUT_S = 30.0  # one model call; less if the turn has less time left

# One client for the whole app: it keeps a pool of HTTP connections open.
# It reads ANTHROPIC_API_KEY from the environment, which the npm scripts load
# from the repo-root .env (`--env-file` in package.json).
# No automatic retries: a retry could run past the turn's deadline. A failed
# call fails the turn, and the customer can send the message again.
client = Anthropic(max_retries=0)


@dataclass(frozen=True)
class Step:
    """One model call, and the tools we ran for it (none on the final step)."""

    request: dict[str, Any]  # exactly the arguments passed to messages.create
    response: Message  # the full API response: content blocks, stop_reason, usage
    latency_s: float
    tool_runs: list[ToolRun]


@dataclass(frozen=True)
class ReplyResult:
    """One turn: the reply for the customer and every step that produced it."""

    text: str  # the reply for the customer, from the last step
    citations: list[Citation]  # the policy lines the reply cites, in order
    steps: list[Step]

    @property
    def response(self) -> Message:
        """The last model response: its stop_reason says how the turn ended."""
        return self.steps[-1].response

    @property
    def is_complete(self) -> bool:
        """True only if the model finished normally (stop_reason "end_turn") with
        some text. A reply cut off at max_tokens, refused, empty, or still asking
        for tools when the loop stopped must not be shown as an answer."""
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

    The API is stateless, so they are attached again on every turn, once, before
    the loop: later messages in the loop are tool results. Earlier messages are
    sent unchanged.
    """
    # Unpacks the last message and the ones before it, like
    # `const latest = messages.at(-1); const history = messages.slice(0, -1)`.
    *history, latest = messages
    if not isinstance(latest["content"], str):
        raise TypeError("The latest message must be plain text")
    content: list[ContentBlockParam] = [
        *as_search_results(documents),
        {"type": "text", "text": latest["content"]},
    ]
    with_attachments: UserMessageParam = {"role": "user", "content": content}
    return [*history, with_attachments]


def tool_round(
    response: Message, customer: Customer
) -> tuple[list[ToolRun], list[MessageParam]]:
    """Runs every tool the response asks for. Returns the runs, and the two
    messages that continue the conversation: the model's response, then one user
    message with a result for each tool call."""
    calls = [block for block in response.content if block.type == "tool_use"]
    runs = [run_tool(call.name, call.input, customer) for call in calls]
    results: list[ToolResultBlockParam] = [
        # tool_use_id ties each result to its call, as the API requires.
        {
            "type": "tool_result",
            "tool_use_id": call.id,
            "content": run.output,
            "is_error": run.is_error,
        }
        for call, run in zip(calls, runs, strict=True)
    ]
    # The response goes back unchanged, including its thinking blocks: the API
    # checks their signatures. Plain dicts, so traces can log it as JSON.
    answered = [
        block.model_dump(mode="json", exclude_none=True) for block in response.content
    ]
    messages: list[MessageParam] = [
        {"role": "assistant", "content": cast(list[ContentBlockParam], answered)},
        {"role": "user", "content": results},
    ]
    return runs, messages


def generate_reply(
    messages: list[MessageParam],
    customer: Customer,
    documents: list[Document] = DOCUMENTS,
) -> ReplyResult:
    """Asks the model for the next reply to the conversation so far.

    `messages` is the full history, oldest first, ending with the customer's
    latest message. `customer` is who is signed in; tools only see their data.
    `documents` are the store's policies; evals can add others, such as one with
    a planted instruction. SDK errors (bad key, rate limit, network, timeout) are
    left for the caller.
    """
    conversation = with_documents(messages, documents)
    steps: list[Step] = []
    turn_started = time.perf_counter()
    for _ in range(MAX_STEPS):
        time_left = TURN_DEADLINE_S - (time.perf_counter() - turn_started)
        if time_left <= 0:
            break  # the last step still asks for tools, so the reply is incomplete
        # Built once and passed as-is, so what callers log is exactly what was
        # sent. A plain dict rather than a typed one: it is only splatted into
        # create().
        request: dict[str, Any] = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "messages": conversation,
            "tools": TOOLS,
            # "summarized" makes thinking blocks carry a readable summary (billed
            # the same as hidden thinking), so eval traces show how the model
            # reasoned. Customers only ever get the text blocks.
            "thinking": {"type": "adaptive", "display": "summarized"},
            "output_config": {"effort": EFFORT},
        }
        started = time.perf_counter()
        # `timeout` is a client option, not part of the API request.
        response = client.messages.create(
            **request, timeout=min(CALL_TIMEOUT_S, time_left)
        )
        latency_s = time.perf_counter() - started

        if response.stop_reason != "tool_use":
            steps.append(Step(request, response, latency_s, tool_runs=[]))
            break
        runs, continuation = tool_round(response, customer)
        steps.append(Step(request, response, latency_s, runs))
        # A new list, so the request logged above keeps the messages it sent.
        conversation = [*conversation, *continuation]

    final = steps[-1].response
    # With citations on, the reply arrives as several text blocks (one per cited
    # stretch); joined, they are the reply. Text from earlier steps is the
    # model narrating its tool calls, so only the last step's text is the reply.
    text = "".join(block.text for block in final.content if block.type == "text")
    return ReplyResult(text=text, citations=citations_in(final, documents), steps=steps)
