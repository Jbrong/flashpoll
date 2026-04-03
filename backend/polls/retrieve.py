from fastapi import APIRouter, HTTPException
from db import get_poll

router = APIRouter()


@router.get("/api/polls/{poll_id}")
def retrieve_poll(poll_id: str) -> dict:
    """
    Gets an existing poll.

    :param poll_id: The poll id to search for.
    :return: A dictionary representing the poll with its info.
    """
    poll_data = get_poll(poll_id)
    if not poll_data:
        raise HTTPException(status_code=404, detail="Failed to retrieve poll data")
    return poll_data