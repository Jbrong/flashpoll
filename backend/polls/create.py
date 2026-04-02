import uuid
import os
from pydantic import BaseModel, Field
from typing import List
from enum import Enum
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from db import save_poll

app_url = os.environ.get('APP_URL')

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
    Creates a new poll based on the provided request data.

    :param poll: The poll creation request containing details like question, answer options, etc.
    :return: A dictionary representing the created poll with its unique identifier and other metadata.
    """
    poll_id = str(uuid.uuid4())
    poll_admin_id = str(uuid.uuid4())
    poll_creation_time = datetime.now(timezone.utc)
    poll_expiry_time = poll_creation_time + timedelta(minutes=poll.poll_expiry)
    poll_expiry_time_iso = poll_expiry_time.isoformat()

    poll_data = {
        "poll_id": poll_id,
        "poll_admin_id": poll_admin_id,
        "poll_question": poll.poll_question,
        "poll_answer_options": poll.poll_answer_options,
        "poll_vote_control": poll.poll_vote_control,
        "poll_results_visibility": poll.poll_results_visibility,
        "poll_expiry_time": poll_expiry_time_iso,
        "share_link": f"{app_url}/poll/{poll_id}",
        "admin_link": f"{app_url}/poll/admin/{poll_admin_id}"
    }

    if not save_poll(poll_data):
        raise HTTPException(status_code=500, detail="Failed to save poll data")
    return poll_data