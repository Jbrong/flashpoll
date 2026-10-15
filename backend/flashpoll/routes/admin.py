from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..deps import get_service
from ..models import AdminPollView
from ..service import PollService

router = APIRouter(prefix="/api/admin/poll", tags=["admin"])

Service = Annotated[PollService, Depends(get_service)]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))]


def _token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    return credentials.credentials if credentials else None


@router.get("")
def get_admin_poll(service: Service, credentials: Credentials) -> AdminPollView:
    return service.admin_view(_token(credentials))


@router.post("/close")
def close_poll(service: Service, credentials: Credentials) -> AdminPollView:
    return service.admin_close(_token(credentials))


@router.delete("", status_code=204)
def delete_poll(service: Service, credentials: Credentials) -> Response:
    service.admin_delete(_token(credentials))
    return Response(status_code=204)
