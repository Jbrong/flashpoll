from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings
from .errors import Forbidden, error_body, register_error_handlers
from .routes import admin, polls
from .security import origin_verified
from .service import PollService
from .store import PollStore


def create_app(settings: Settings | None = None, store: PollStore | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Flashpoll API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.settings = settings
    app.state.service = PollService(store or PollStore(settings), settings)

    @app.middleware("http")
    async def require_origin_secret(request: Request, call_next):
        # In AWS only CloudFront knows this secret, so the API can't be called around it
        # (which would also let callers forge the client IP header).
        if not origin_verified(
            request.headers.get("x-origin-verify"), settings.origin_verify_secret
        ):
            denied = Forbidden()
            return JSONResponse(error_body(denied.code, denied.message), status_code=denied.status)
        return await call_next(request)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type", "X-Admin-Token", "X-Voter-Token"],
        )

    register_error_handlers(app)
    app.include_router(polls.router)
    app.include_router(admin.router)

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    return app
