from fastapi import Request

from .config import Settings
from .service import PollService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_service(request: Request) -> PollService:
    return request.app.state.service
