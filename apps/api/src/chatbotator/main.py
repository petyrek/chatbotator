from fastapi import FastAPI

from chatbotator.routes import chat, health

# uvicorn serves this object: `uvicorn chatbotator.main:app`.
app = FastAPI(title="Chatbotator API")
app.include_router(health.router)
app.include_router(chat.router)
