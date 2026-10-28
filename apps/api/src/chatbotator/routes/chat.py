import logging
from typing import Literal

import anthropic
from anthropic.types import MessageParam
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from chatbotator.chat.reply import ReplyResult, generate_reply

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    # Long enough for any model reply (max_tokens 4096 is roughly 16k characters),
    # since earlier replies come back in later requests. The widget limits what
    # customers type to 1000 characters.
    content: str = Field(min_length=1, max_length=20_000)


class ChatRequest(BaseModel):
    # The widget offers "Start a new conversation" before reaching this limit.
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)

    @field_validator("messages")
    @classmethod
    def starts_and_ends_with_user(
        cls, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        if messages[0].role != "user" or messages[-1].role != "user":
            raise ValueError("The conversation must start and end with a user message.")
        return messages


class CitationOut(BaseModel):
    document: str
    title: str
    section: str
    quote: str


class ChatResponse(BaseModel):
    reply: str
    citations: list[CitationOut]  # the policy lines the reply rests on


def to_model_message(message: ChatMessage) -> MessageParam:
    # The SDK has a separate type per role (like a TS discriminated union), so
    # each branch builds a dict whose role mypy knows exactly.
    if message.role == "user":
        return {"role": "user", "content": message.content}
    return {"role": "assistant", "content": message.content}


def is_complete(result: ReplyResult) -> bool:
    """The call succeeded, but the reply may still be unusable: cut off at
    max_tokens, refused, or empty. Never show half an answer as a success."""
    return result.response.stop_reason == "end_turn" and bool(result.text.strip())


def to_response(result: ReplyResult) -> ChatResponse:
    citations = [CitationOut(**vars(citation)) for citation in result.citations]
    return ChatResponse(reply=result.text, citations=citations)


@router.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    history = [to_model_message(message) for message in request.messages]
    try:
        result = generate_reply(history)
    except anthropic.AuthenticationError as error:
        logger.error("Model call rejected: check ANTHROPIC_API_KEY in .env")
        raise HTTPException(
            500, "The assistant is not configured correctly."
        ) from error
    except anthropic.RateLimitError as error:
        logger.warning("Model call rate-limited")
        raise HTTPException(
            503, "The assistant is busy. Please try again shortly."
        ) from error
    except anthropic.APIError as error:
        logger.exception("Model call failed")
        raise HTTPException(502, "The assistant is unavailable right now.") from error

    if not is_complete(result):
        logger.warning("Incomplete reply (stop_reason=%s)", result.response.stop_reason)
        raise HTTPException(
            502, "The assistant couldn't finish its answer. Please try again."
        )
    return to_response(result)
