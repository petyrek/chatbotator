from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/api/chat")
def chat() -> None:
    # YOUR EXERCISE: implement the first model-backed endpoint here.
    # Keep this handler thin: validate the request with a Pydantic model, call
    # into chatbotator.chat, and return its result. The eval runner should be
    # able to call that same chat code directly, without going through HTTP.
    # Keep credentials on the server. Do not trust a client-supplied customer ID.
    raise HTTPException(status_code=501, detail="Your model integration starts here.")
