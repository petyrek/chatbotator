from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from chatbotator.routes import chat, health


def create_app() -> FastAPI:
    app = FastAPI(title="Chatbotator API")
    app.include_router(health.router)
    app.include_router(chat.router)

    @app.middleware("http")
    async def no_store(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


app = create_app()
