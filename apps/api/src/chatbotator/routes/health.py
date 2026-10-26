from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Health(BaseModel):
    status: Literal["ok"]
    service: str


# The return type annotation doubles as the response schema (see /docs).
@router.get("/api/health")
def health() -> Health:
    return Health(status="ok", service="chatbotator-api")
