from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .errors import register_error_handlers
from .routes import admin, polls
from .service import PollService
from .store import PollStore


def create_app(settings: Settings | None = None, store: PollStore | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Flashpoll API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.settings = settings
    app.state.service = PollService(store or PollStore(settings), settings)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type", "Authorization", "X-Voter-Token"],
        )

    register_error_handlers(app)
    app.include_router(polls.router)
    app.include_router(admin.router)

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    return app
