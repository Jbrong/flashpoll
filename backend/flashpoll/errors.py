import logging

from botocore.exceptions import ClientError
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """An error with a stable machine-readable code (see docs/spec.md, section 2.1)."""

    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message


class PollNotFound(ApiError):
    def __init__(self):
        super().__init__(404, "poll_not_found", "Poll not found")


class PollClosed(ApiError):
    def __init__(self):
        super().__init__(409, "poll_closed", "This poll is closed")


class AlreadyVoted(ApiError):
    def __init__(self):
        super().__init__(409, "already_voted", "You have already voted on this poll")


class ResultsHidden(ApiError):
    def __init__(self):
        super().__init__(403, "results_hidden", "Results are not visible yet")


class Forbidden(ApiError):
    def __init__(self):
        super().__init__(403, "forbidden", "Requests must come through flashpoll.dev")


class Unauthorized(ApiError):
    def __init__(self):
        super().__init__(401, "unauthorized", "Invalid or missing admin token")


# DynamoDB capacity errors: provisioned throughput is small (always-free tier), so a burst
# can exhaust it after boto3's own retries. Tell the client to retry instead of a bare 500.
THROTTLE_CODES = {
    "ProvisionedThroughputExceededException",
    "ThrottlingException",
    "RequestLimitExceeded",
}
THROTTLE_REASONS = {"ThrottlingError", "ProvisionedThroughputExceeded"}


def is_throttle(err: ClientError) -> bool:
    if err.response.get("Error", {}).get("Code") in THROTTLE_CODES:
        return True
    reasons = err.response.get("CancellationReasons", [])
    return any(reason.get("Code") in THROTTLE_REASONS for reason in reasons)


def error_body(code: str, message: str, **extra) -> dict:
    return {"error": {"code": code, "message": message, **extra}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError):
        return JSONResponse(error_body(exc.code, exc.message), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        fields = [
            {"loc": [str(part) for part in err["loc"]], "message": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            error_body("invalid_request", "Request is invalid", fields=fields), status_code=422
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(error_body(code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(ClientError)
    async def aws_error(_: Request, exc: ClientError):
        if is_throttle(exc):
            logger.warning("DynamoDB throttled: %s", exc)
            return JSONResponse(
                error_body("busy", "Flashpoll is busy right now. Try again in a moment."),
                status_code=503,
                headers={"Retry-After": "2"},
            )
        logger.exception("AWS error", exc_info=exc)
        return JSONResponse(error_body("internal_error", "Something went wrong"), status_code=500)

    @app.exception_handler(Exception)
    async def unhandled_error(_: Request, exc: Exception):
        logger.exception("Unhandled error", exc_info=exc)
        return JSONResponse(error_body("internal_error", "Something went wrong"), status_code=500)
