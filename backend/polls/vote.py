import uuid
from pydantic import BaseModel
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from db import save_vote, get_poll

class Vote(BaseModel):
    selected_option: str

router = APIRouter()

@router.post("/api/polls/{poll_id}/vote")
def vote(poll_id: str, vote: Vote) -> bool:
    """
    Take in vote from poll and save to Dynamodb "votes" table
    :param poll_id: The poll id
    :param vote: The vote info
    :return: True if vote is saved successfully
    """
    poll_data = get_poll(poll_id)
    if not poll_data:
        raise HTTPException(status_code=404, detail="Poll not found")

    vote.selected_option = vote.selected_option.lower()
    if vote.selected_option not in poll_data['poll_answer_options']:
        raise HTTPException(status_code=400, detail="Invalid option selected")

    vote_id = str(uuid.uuid4())
    vote_time = datetime.now(timezone.utc).isoformat()

    if not save_vote(poll_id, vote.selected_option, vote_id, vote_time):
        raise HTTPException(status_code=500, detail="Failed to save poll data")
    return True
