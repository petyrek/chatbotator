"""Tests for generate_reply, the boundary between our code and the model API.
The SDK client is replaced by a fake, so nothing is sent over the network."""

from types import SimpleNamespace
from typing import Any

import pytest
from anthropic.types import Message, TextBlock, ThinkingBlock

from chatbotator.chat import reply


def test_sends_the_conversation_and_returns_only_the_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: dict[str, Any] = {}

    def fake_create(**request: Any) -> Message:
        sent.update(request)
        return Message.model_construct(
            content=[
                ThinkingBlock.model_construct(
                    type="thinking", thinking="Plan the answer."
                ),
                TextBlock.model_construct(type="text", text="Hello "),
                TextBlock.model_construct(type="text", text="Martin!"),
            ],
            stop_reason="end_turn",
        )

    fake_client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(reply, "client", fake_client)
    conversation: Any = [{"role": "user", "content": "Hi, I'm Martin."}]

    result = reply.generate_reply(conversation)

    assert result.text == "Hello Martin!"  # thinking is never part of the reply
    assert sent["model"] == reply.MODEL
    assert sent["system"] == reply.SYSTEM_PROMPT
    assert sent["messages"] == conversation
    assert result.request == sent  # what we record is exactly what was sent
    assert result.response.stop_reason == "end_turn"
