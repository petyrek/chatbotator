"""POST /api/chat: validates the conversation, asks the assistant for a reply,
and turns model failures into errors the chat widget can show."""

import logging
from typing import Annotated, Literal

import anthropic
from anthropic.types import MessageParam
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from chatbotator.assistant.reply import ReplyResult, generate_reply
from chatbotator.customers import Customer, current_customer

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    # Earlier replies come back in later requests, so allow any reply
    # (max_tokens 4096 ≈ 16k characters). The widget caps typing at 1000.
    content: str = Field(min_length=1, max_length=20_000)


class ChatRequest(BaseModel):
    # The widget offers "Start a new conversation" before reaching this limit.
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)

    # Runs after the field's own checks; a ValueError here becomes a 422.
    @field_validator("messages")
    @classmethod
    def starts_and_ends_with_user(
        cls, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        if messages[0].role != "user" or messages[-1].role != "user":
            raise ValueError("The conversation must start and end with a user message.")
        return messages


# The response shapes below are mirrored in apps/web/src/api.ts. They are kept
# separate from the assistant's own types, so the HTTP contract only changes
# when we change it here.
class CitationOut(BaseModel):  # `Citation` in api.ts
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


def to_response(result: ReplyResult) -> ChatResponse:
    citations = [
        CitationOut(
            document=citation.document,
            title=citation.title,
            section=citation.section,
            quote=citation.quote,
        )
        for citation in result.citations
    ]
    return ChatResponse(reply=result.text, citations=citations)


# FastAPI validates the JSON body into ChatRequest (422 if invalid) and turns
# the returned ChatResponse into JSON. `Depends(current_customer)` makes FastAPI
# call current_customer() and pass in who is signed in: the server decides, not
# the request body.
@router.post("/api/chat")
def post_chat(
    request: ChatRequest, customer: Annotated[Customer, Depends(current_customer)]
) -> ChatResponse:
    history = [to_model_message(message) for message in request.messages]
    # Each SDK error becomes a message that is safe to show the customer; the
    # details go only to the server log (and never the API key).
    try:
        result = generate_reply(history, customer)
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
    # APIError is the base class, so it comes last and catches the rest
    # (timeouts, connection errors, 5xx).
    except anthropic.APIError as error:
        logger.exception("Model call failed")
        raise HTTPException(502, "The assistant is unavailable right now.") from error

    if not result.is_complete:
        logger.warning("Incomplete reply (stop_reason=%s)", result.response.stop_reason)
        raise HTTPException(
            502, "The assistant couldn't finish its answer. Please try again."
        )
    return to_response(result)
