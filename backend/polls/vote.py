import uuid
from pydantic import BaseModel
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from db import save_vote, get_poll, get_votes

class Vote(BaseModel):
    selected_option: str

router = APIRouter()

@router.post("/api/polls/{poll_id}/vote")
def vote(poll_id: str, vote: Vote, request: Request) -> bool:
    """
    Take in vote from poll and save to Dynamodb "votes" table
    :param poll_id: The poll id
    :param vote: The vote info
    :return: True if vote is saved successfully
    """
    poll_data = get_poll(poll_id)
    if not poll_data:
        raise HTTPException(status_code=404, detail="Poll not found")

    check_vote_expiration(poll_data)
    check_vote_control(poll_data, poll_id, request)

    vote.selected_option = vote.selected_option.lower()
    if vote.selected_option not in poll_data['poll_answer_options']:
        raise HTTPException(status_code=400, detail="Invalid option selected")

    vote_id = str(uuid.uuid4())
    vote_time = datetime.now(timezone.utc).isoformat()
    client_ip = request.client.host

    if not save_vote(poll_id, vote.selected_option, vote_id, vote_time, client_ip):
        raise HTTPException(status_code=500, detail="Failed to save poll data")
    return True


def check_vote_expiration(poll_data: dict) -> bool:
    if datetime.now(timezone.utc) > datetime.fromisoformat(poll_data['poll_expiry_time']):
        raise HTTPException(status_code=403, detail="Poll has expired")

def check_vote_control(poll_data: dict, poll_id: str, request: Request) -> bool:
    vote_data = get_votes(poll_id)
    poll_control = poll_data['poll_vote_control']
    if poll_control == 'one_per_ip':
        for result in vote_data:
            if result['client_ip'] == request.client.host:
                raise HTTPException(status_code=403, detail="Voting is restricted to once per IP address")
