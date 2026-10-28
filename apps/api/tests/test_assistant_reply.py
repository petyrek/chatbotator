"""Tests for generate_reply, the boundary between our code and the model API.
The SDK client is replaced by a fake, so nothing is sent over the network."""

from types import SimpleNamespace
from typing import Any

import pytest
from anthropic.types import (
    CitationsSearchResultLocation,
    Message,
    MessageParam,
    TextBlock,
    ThinkingBlock,
)

from chatbotator.assistant import reply
from chatbotator.assistant.citations import Citation
from chatbotator.policies import DOCUMENTS, Document, Passage


def fake_client(sent: dict[str, Any], content: list[Any]) -> SimpleNamespace:
    """Stands in for the Anthropic client: client.messages.create(...) records
    its arguments into `sent` and returns a response holding `content`."""

    def create(**request: Any) -> Message:
        sent.update(request)
        # model_construct() builds the SDK object without validation.
        return Message.model_construct(content=content, stop_reason="end_turn")

    return SimpleNamespace(messages=SimpleNamespace(create=create))


def test_attaches_all_documents_to_the_latest_message_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: dict[str, Any] = {}
    # generate_reply looks up the module-level `client` when it runs, so
    # replacing it here makes it use the fake.
    monkeypatch.setattr(reply, "client", fake_client(sent, []))
    conversation: list[MessageParam] = [
        {"role": "user", "content": "Do you ship to Czechia?"},
        {"role": "assistant", "content": "Yes."},
        {"role": "user", "content": "How much?"},
    ]

    result = reply.generate_reply(conversation)

    assert sent["messages"][:2] == conversation[:2]  # history unchanged
    *documents, question = sent["messages"][2]["content"]
    assert [d["source"] for d in documents] == [d.name for d in DOCUMENTS]
    assert all(d["citations"] == {"enabled": True} for d in documents)
    assert question == {"type": "text", "text": "How much?"}
    assert result.request == sent  # what we record is exactly what was sent


def test_the_reply_is_the_text_blocks_joined_without_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # With citations on, one reply arrives as several text blocks.
    content = [
        ThinkingBlock.model_construct(type="thinking", thinking="Check the policy."),
        TextBlock.model_construct(type="text", text="You have 30 days", citations=None),
        TextBlock.model_construct(
            type="text", text=", counted from delivery.", citations=None
        ),
    ]
    monkeypatch.setattr(reply, "client", fake_client({}, content))

    result = reply.generate_reply([{"role": "user", "content": "How long?"}])

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
    content = [TextBlock.model_construct(type="text", text="12.", citations=[cited])]
    sent: dict[str, Any] = {}
    monkeypatch.setattr(reply, "client", fake_client(sent, content))

    result = reply.generate_reply(
        [{"role": "user", "content": "Pegs?"}], [*DOCUMENTS, extra]
    )

    *documents, _ = sent["messages"][0]["content"]
    assert documents[-1]["source"] == "note.md"
    assert result.citations == [
        Citation("note.md", "Supplier note", "Details", "Details: 12 pegs.")
    ]
