import pytest

from flashpoll.security import hash_admin_token
from flashpoll.tables import ADMIN_INDEX  # noqa: F401  (schema import smoke check)


def test_create_returns_links_and_expiry(make_poll):
    poll = make_poll(expires_in_minutes=90)
    assert len(poll["poll_id"]) == 8
    assert len(poll["admin_token"]) == 32
    assert poll["share_url"] == f"https://flashpoll.test/p/{poll['poll_id']}"
    assert poll["admin_url"] == f"https://flashpoll.test/admin#{poll['admin_token']}"
    assert poll["expires_at"] == "2027-01-15T09:30:00Z"


def test_create_stores_hash_not_admin_token_and_sets_ttl(make_poll, aws):
    poll = make_poll(expires_in_minutes=60)
    item = aws.get_item(TableName="flashpoll-polls", Key={"poll_id": {"S": poll["poll_id"]}})[
        "Item"
    ]
    assert item["admin_token_hash"]["S"] == hash_admin_token(poll["admin_token"])
    assert poll["admin_token"] not in str(item)
    assert int(item["ttl"]["N"]) == int(item["expires_at"]["N"]) + 24 * 3600


def test_create_defaults(client):
    response = client.post(
        "/api/polls", json={"question": "Q", "options": ["A", "B"], "expires_in_minutes": 15}
    )
    assert response.status_code == 201
    poll = client.get(f"/api/polls/{response.json()['poll_id']}").json()
    assert poll["vote_control"] == "one_per_browser"
    assert poll["results_visibility"] == "live"


def test_create_trims_whitespace_and_keeps_case(client, make_poll):
    poll = make_poll(question="  Lunch?  ", options=["  Pizza ", "TACOS"])
    view = client.get(f"/api/polls/{poll['poll_id']}").json()
    assert view["question"] == "Lunch?"
    assert view["options"] == ["Pizza", "TACOS"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"question": "   "},
        {"question": "x" * 201},
        {"options": ["Only one"]},
        {"options": ["A", "B", "C", "D", "E", "F", "G"]},
        {"options": ["A", " "]},
        {"options": ["A", "x" * 101]},
        {"options": ["Pizza", "pizza"]},
        {"expires_in_minutes": 14},
        {"expires_in_minutes": 15 * 24 * 60 + 1},
        {"vote_control": "one_per_planet"},
        {"results_visibility": "sometimes"},
    ],
)
def test_create_rejects_invalid_input(client, overrides):
    body = {"question": "Q", "options": ["A", "B"], "expires_in_minutes": 60, **overrides}
    response = client.post("/api/polls", json=body)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request"
    assert error["fields"]


def test_create_accepts_limits(make_poll):
    make_poll(options=["A", "B"], expires_in_minutes=15)
    make_poll(options=list("ABCDEF"), expires_in_minutes=15 * 24 * 60, question="x" * 200)
