from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request

from ..config import Settings
from ..deps import get_service, get_settings
from ..models import (
    CreatePollRequest,
    CreatePollResponse,
    PollView,
    ResultsResponse,
    VoteRequest,
    VoteResponse,
)
from ..security import client_ip
from ..service import PollService

router = APIRouter(prefix="/api/polls", tags=["polls"])

Service = Annotated[PollService, Depends(get_service)]
VoterToken = Annotated[
    str | None,
    Header(alias="X-Voter-Token", min_length=16, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
]


@router.post("", status_code=201)
def create_poll(body: CreatePollRequest, service: Service) -> CreatePollResponse:
    return service.create_poll(body)


@router.get("/{poll_id}")
def get_poll(poll_id: str, service: Service, voter_token: VoterToken = None) -> PollView:
    return service.get_poll(poll_id, voter_token)


@router.post("/{poll_id}/votes")
def vote(
    poll_id: str,
    body: VoteRequest,
    request: Request,
    service: Service,
    settings: Annotated[Settings, Depends(get_settings)],
    voter_token: VoterToken = None,
) -> VoteResponse:
    ip = client_ip(request, settings.trusted_proxy_count)
    return VoteResponse(results=service.vote(poll_id, body.option_index, voter_token, ip))


@router.get("/{poll_id}/results")
def get_results(poll_id: str, service: Service, voter_token: VoterToken = None) -> ResultsResponse:
    return service.get_results(poll_id, voter_token)
