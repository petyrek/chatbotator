import logging
from typing import Literal

import anthropic
from anthropic.types import MessageParam
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from chatbotator.chat.reply import generate_reply

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)

    @field_validator("messages")
    @classmethod
    def starts_and_ends_with_user(
        cls, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        if messages[0].role != "user" or messages[-1].role != "user":
            raise ValueError("The conversation must start and end with a user message.")
        return messages


class ChatResponse(BaseModel):
    reply: str


def to_model_message(message: ChatMessage) -> MessageParam:
    # The SDK has a separate type per role (like a TS discriminated union), so
    # each branch builds a dict whose role mypy knows exactly.
    if message.role == "user":
        return {"role": "user", "content": message.content}
    return {"role": "assistant", "content": message.content}


@router.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    history = [to_model_message(message) for message in request.messages]
    try:
        reply = generate_reply(history)
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
    return ChatResponse(reply=reply)
