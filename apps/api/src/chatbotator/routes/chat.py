from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/api/chat")
def chat() -> JSONResponse:
    # YOUR EXERCISE: implement the first model-backed endpoint here.
    # Keep this handler thin: validate the request with a Pydantic model, call
    # into chatbotator.chat, and return its result. The eval runner should be
    # able to call that same chat code directly, without going through HTTP.
    # Keep credentials on the server. Do not trust a client-supplied customer ID.
    return JSONResponse(
        status_code=501,
        content={
            "error": "NOT_IMPLEMENTED",
            "message": "Your model integration starts here.",
        },
    )
