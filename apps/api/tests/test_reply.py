"""Tests for generate_reply, the boundary between our code and the model API.
The SDK client is replaced by a fake, so nothing is sent over the network."""

from types import SimpleNamespace
from typing import Any

import pytest
from anthropic.types import (
    CitationsSearchResultLocation,
    Message,
    TextBlock,
    ThinkingBlock,
)

from chatbotator.chat import reply
from chatbotator.knowledge.documents import DOCUMENTS, Document, Passage


def returns_citation(block: int) -> CitationsSearchResultLocation:
    index = [d.name for d in DOCUMENTS].index("returns.md")
    return CitationsSearchResultLocation.model_construct(
        type="search_result_location",
        cited_text=f"cited line {block}",
        search_result_index=index,
        start_block_index=block,
        end_block_index=block + 1,
    )


def fake_client(sent: dict[str, Any], content: list[Any]) -> SimpleNamespace:
    def create(**request: Any) -> Message:
        sent.update(request)
        return Message.model_construct(content=content, stop_reason="end_turn")

    return SimpleNamespace(messages=SimpleNamespace(create=create))


def test_attaches_all_documents_to_the_latest_message_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: dict[str, Any] = {}
    monkeypatch.setattr(reply, "client", fake_client(sent, []))
    conversation: Any = [
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


def test_returns_only_the_text_and_the_cited_policy_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = [
        ThinkingBlock.model_construct(type="thinking", thinking="Check the policy."),
        TextBlock.model_construct(
            type="text", text="You have 30 days", citations=[returns_citation(0)]
        ),
        TextBlock.model_construct(
            type="text", text=", counted from delivery.", citations=None
        ),
        TextBlock.model_construct(
            type="text", text=" Day 0!", citations=[returns_citation(0)]
        ),
    ]
    monkeypatch.setattr(reply, "client", fake_client({}, content))
    returns = next(d for d in DOCUMENTS if d.name == "returns.md")

    result = reply.generate_reply([{"role": "user", "content": "How long?"}])

    assert result.text == "You have 30 days, counted from delivery. Day 0!"
    assert len(result.citations) == 1  # the same line cited twice is listed once
    assert result.citations[0].document == "returns.md"
    assert result.citations[0].section == returns.passages[0].section
    assert result.citations[0].quote == "cited line 0"


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
        reply.Citation("note.md", "Supplier note", "Details", "Details: 12 pegs.")
    ]
