from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

MIN_EXPIRY_MINUTES = 15
MAX_EXPIRY_MINUTES = 15 * 24 * 60

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Option = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class VoteControl(StrEnum):
    open = "open"
    one_per_browser = "one_per_browser"
    one_per_ip = "one_per_ip"


class ResultsVisibility(StrEnum):
    live = "live"
    after_voting = "after_voting"
    private = "private"


class PollStatus(StrEnum):
    open = "open"
    closed = "closed"


class CreatePollRequest(BaseModel):
    question: Question
    options: list[Option] = Field(min_length=2, max_length=6)
    expires_in_minutes: int = Field(ge=MIN_EXPIRY_MINUTES, le=MAX_EXPIRY_MINUTES)
    vote_control: VoteControl = VoteControl.one_per_browser
    results_visibility: ResultsVisibility = ResultsVisibility.live

    @field_validator("options")
    @classmethod
    def options_unique(cls, options: list[str]) -> list[str]:
        if len({option.casefold() for option in options}) != len(options):
            raise ValueError("Options must be unique")
        return options


class CreatePollResponse(BaseModel):
    poll_id: str
    admin_token: str
    share_url: str
    admin_url: str
    expires_at: str


class Results(BaseModel):
    total_votes: int
    counts: list[int]


class ResultsResponse(Results):
    status: PollStatus


class PollView(BaseModel):
    poll_id: str
    question: str
    options: list[str]
    vote_control: VoteControl
    results_visibility: ResultsVisibility
    created_at: str
    expires_at: str
    status: PollStatus
    has_voted: bool
    results_available: bool


class AdminPollView(PollView):
    results: Results
    deletes_at: str


class VoteRequest(BaseModel):
    option_index: int = Field(ge=0)


class VoteResponse(BaseModel):
    results: Results | None
