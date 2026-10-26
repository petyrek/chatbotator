from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Health(BaseModel):
    status: Literal["ok"]
    service: str
    aiConnected: bool


@router.get("/api/health")
def health() -> Health:
    return Health(status="ok", service="chatbotator-api", aiConnected=False)
