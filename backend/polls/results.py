"""
take incomine request via router
check results for poll by using db.py get_votes
tally votes
return something for the front end
"""

from collections import Counter
from db import get_votes, get_poll
from fastapi import APIRouter, HTTPException


router = APIRouter()

@router.get("/api/polls/{poll_id}/results")
def process_results(poll_id: str) -> dict:
    try:
        vote_data = retrieve_results(poll_id)
    except Exception as e:
        print(f"Error processing results: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve poll results")
    try:
        results = tally_votes(vote_data)
    except Exception as e:
        print(f"Error tallying votes: {e}")
        raise HTTPException(status_code=500, detail="Failed to tally votes")
    return results

def retrieve_results(poll_id: str) -> dict:
    if get_poll(poll_id) is None:
        raise HTTPException(status_code=404, detail="Poll not found")
    return get_votes(poll_id)

def tally_votes(votes: list) -> dict:
    return Counter(vote['vote_info'] for vote in votes)
