from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response

from ..deps import get_service
from ..models import AdminPollView
from ..service import PollService

router = APIRouter(prefix="/api/admin/poll", tags=["admin"])

Service = Annotated[PollService, Depends(get_service)]
# A custom header rather than `Authorization`, so CloudFront can forward it with a plain
# origin request policy allowlist (docs/spec.md, 2.2).
AdminToken = Annotated[str | None, Header(alias="X-Admin-Token", max_length=128)]


@router.get("")
def get_admin_poll(service: Service, admin_token: AdminToken = None) -> AdminPollView:
    return service.admin_view(admin_token)


@router.post("/close")
def close_poll(service: Service, admin_token: AdminToken = None) -> AdminPollView:
    return service.admin_close(admin_token)


@router.delete("", status_code=204)
def delete_poll(service: Service, admin_token: AdminToken = None) -> Response:
    service.admin_delete(admin_token)
    return Response(status_code=204)
