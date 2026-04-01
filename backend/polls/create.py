import uuid
from pydantic import BaseModel, Field
from typing import List
from enum import Enum
from datetime import datetime, timedelta
from fastapi import APIRouter


class VoteControl(str, Enum):
    no_restrictions = "open"
    cookie_based = "one_per_browser"
    ip_based = "one_per_ip"


class ResultsVisibility(str, Enum):
    live = "live"
    after_voting = "after_voting"
    private = "private"


class CreatePollRequest(BaseModel):
    poll_question: str
    poll_answer_options: List[str]
    poll_vote_control: VoteControl
    poll_results_visibility : ResultsVisibility
    poll_expiry: int = Field(ge=15, le=21600)


router = APIRouter()


@router.post("/api/polls")
def create_poll(poll: CreatePollRequest) -> dict:
    """
    TODO: return poll_question and poll_answer_options so we can store in db
    TODO: update date time to datetime.now(timezone.utc)
    TODO: Dynamically generate share link and admin link for local dev and prod
    Creates a new poll based on the provided request data.

    :param poll: The poll creation request containing details like question, answer options, etc.
    :return: A dictionary representing the created poll with its unique identifier and other metadata.
    """
    poll_id = str(uuid.uuid4())
    poll_admin_id = str(uuid.uuid4())
    poll_creation_time = datetime.utcnow()
    poll_expiry_time = poll_creation_time + timedelta(minutes=poll.poll_expiry)
    return {
        "poll_id": poll_id,
        "poll_admin_id": poll_admin_id,
        "poll_vote_control": poll.poll_vote_control,
        "poll_results_visibility": poll.poll_results_visibility,
        "poll_expiry_time": poll_expiry_time,
        "share_link": f"https://flashpoll.com/poll/{poll_id}",
        "admin_link": f"https://flashpoll.com/poll/admin/{poll_admin_id}"
    }