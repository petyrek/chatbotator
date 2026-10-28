"""Tests for generate_reply: the loop of model calls and tool calls.
The SDK client is replaced by a fake, so nothing is sent over the network."""

import json
import time
from types import SimpleNamespace
from typing import Any

import pytest
from anthropic.types import (
    CitationsSearchResultLocation,
    Message,
    MessageParam,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
)

from chatbotator.assistant import reply
from chatbotator.assistant.citations import Citation
from chatbotator.customers import CUSTOMERS
from chatbotator.policies import DOCUMENTS, Document, Passage

ALEX = CUSTOMERS["customer-alex"]
QUESTION: list[MessageParam] = [{"role": "user", "content": "Where's TS-1001?"}]


def answer(*blocks: Any) -> Message:
    """A final response. model_construct() builds SDK objects without validation."""
    return Message.model_construct(content=list(blocks), stop_reason="end_turn")


def text(value: str) -> TextBlock:
    return TextBlock.model_construct(type="text", text=value, citations=None)


def asks_for_order(order_id: str) -> Message:
    """A response asking to run get_order, after thinking about it."""
    return Message.model_construct(
        content=[
            ThinkingBlock.model_construct(
                type="thinking", thinking="Look it up.", signature="sig"
            ),
            ToolUseBlock.model_construct(
                type="tool_use",
                id="call-1",
                name="get_order",
                input={"order_id": order_id},
            ),
        ],
        stop_reason="tool_use",
    )


def fake_model(
    monkeypatch: pytest.MonkeyPatch, *responses: Message
) -> list[dict[str, Any]]:
    """Replaces the client: each messages.create(...) returns the next response
    (the last one repeats) and its arguments are recorded in the returned list."""
    calls: list[dict[str, Any]] = []

    def create(**request: Any) -> Message:
        calls.append(request)
        return responses[min(len(calls), len(responses)) - 1]

    # generate_reply looks up the module-level `client` when it runs, so
    # replacing it here makes it use the fake.
    fake = SimpleNamespace(messages=SimpleNamespace(create=create))
    monkeypatch.setattr(reply, "client", fake)
    return calls


def test_attaches_all_documents_to_the_latest_message_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_model(monkeypatch, answer(text("€5.")))
    conversation: list[MessageParam] = [
        {"role": "user", "content": "Do you ship to Czechia?"},
        {"role": "assistant", "content": "Yes."},
        {"role": "user", "content": "How much?"},
    ]

    result = reply.generate_reply(conversation, ALEX)

    sent = calls[0]["messages"]
    assert sent[:2] == conversation[:2]  # history unchanged
    *documents, question = sent[2]["content"]
    assert [d["source"] for d in documents] == [d.name for d in DOCUMENTS]
    assert question == {"type": "text", "text": "How much?"}
    assert {**result.steps[0].request, "timeout": 30.0} == calls[0]  # logged = sent


def test_runs_the_tool_and_sends_its_result_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_model(
        monkeypatch, asks_for_order("TS-1001"), answer(text("It arrived."))
    )

    result = reply.generate_reply(QUESTION, ALEX)

    assert result.text == "It arrived."
    assert result.is_complete
    assert [run.name for run in result.steps[0].tool_runs] == ["get_order"]
    # The second call repeats the conversation, plus the model's response
    # (thinking included, signature intact) and our tool result.
    *_, asked, results = calls[1]["messages"]
    assert asked["role"] == "assistant"
    assert asked["content"][0]["signature"] == "sig"
    [result_block] = results["content"]
    assert result_block["tool_use_id"] == "call-1"
    assert json.loads(result_block["content"])["order_id"] == "TS-1001"
    assert result_block["is_error"] is False


def test_a_failed_tool_goes_back_to_the_model_as_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_model(
        monkeypatch, asks_for_order("TS-1003"), answer(text("I can't find it."))
    )

    reply.generate_reply(QUESTION, ALEX)

    [result_block] = calls[1]["messages"][-1]["content"]
    assert result_block["is_error"] is True
    assert result_block["content"] == "No order TS-1003 found for this customer."


def test_stops_after_max_steps_with_an_incomplete_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_model(monkeypatch, asks_for_order("TS-1001"))  # asks forever

    result = reply.generate_reply(QUESTION, ALEX)

    assert len(calls) == reply.MAX_STEPS
    assert not result.is_complete


def test_stops_when_the_turn_runs_out_of_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]  # a fake clock: every model call takes 40 s

    def slow_create(**request: Any) -> Message:
        clock[0] += 40
        return asks_for_order("TS-1001")

    fake = SimpleNamespace(messages=SimpleNamespace(create=slow_create))
    monkeypatch.setattr(reply, "client", fake)
    # Replaces time.perf_counter everywhere until the test ends.
    monkeypatch.setattr(time, "perf_counter", lambda: clock[0])

    result = reply.generate_reply(QUESTION, ALEX)

    # 60 s deadline: call 1 at 0 s, call 2 at 40 s, none at 80 s.
    assert len(result.steps) == 2
    assert not result.is_complete


def test_the_reply_is_the_last_steps_text_without_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # With citations on, one reply arrives as several text blocks.
    fake_model(
        monkeypatch,
        answer(
            ThinkingBlock.model_construct(type="thinking", thinking="Policy."),
            text("You have 30 days"),
            text(", counted from delivery."),
        ),
    )

    result = reply.generate_reply(QUESTION, ALEX)

    assert result.text == "You have 30 days, counted from delivery."


def test_each_passage_is_one_citable_block_that_names_its_section() -> None:
    document = Document(
        "returns.md",
        "Returns & refunds",
        [
            Passage("Return window", "Day 0 is delivery."),
            Passage("Condition", "Unused."),
        ],
    )

    [result] = reply.as_search_results([document])

    assert result["source"] == "returns.md"
    assert result["citations"] == {"enabled": True}
    assert [block["text"] for block in result["content"]] == [
        "Return window: Day 0 is delivery.",
        "Condition: Unused.",
    ]


def test_extra_documents_are_sent_after_the_store_and_cited_by_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extra = Document("note.md", "Supplier note", [Passage("Details", "12 pegs.")])
    cited = CitationsSearchResultLocation.model_construct(
        type="search_result_location",
        cited_text="Details: 12 pegs.",
        search_result_index=len(DOCUMENTS),  # the first document after the store's
        start_block_index=0,
        end_block_index=1,
    )
    block = TextBlock.model_construct(type="text", text="12.", citations=[cited])
    calls = fake_model(monkeypatch, answer(block))

    result = reply.generate_reply(QUESTION, ALEX, [*DOCUMENTS, extra])

    *documents, _ = calls[0]["messages"][0]["content"]
    assert documents[-1]["source"] == "note.md"
    assert result.citations == [
        Citation("note.md", "Supplier note", "Details", "Details: 12 pegs.")
    ]
