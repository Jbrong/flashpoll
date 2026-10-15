from conftest import VOTER_A, vote


def test_get_poll_public_view_has_no_admin_data(client, make_poll):
    poll = make_poll()
    response = client.get(f"/api/polls/{poll['poll_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "poll_id": poll["poll_id"],
        "question": "Lunch?",
        "options": ["Pizza", "Tacos", "Salad"],
        "vote_control": "open",
        "results_visibility": "live",
        "created_at": "2027-01-15T08:00:00Z",
        "expires_at": "2027-01-15T09:00:00Z",
        "status": "open",
        "has_voted": False,
        "results_available": True,
    }
    assert poll["admin_token"] not in response.text


def test_unknown_poll_is_404(client):
    response = client.get("/api/polls/nope1234")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "poll_not_found"
    assert client.get("/api/polls/nope1234/results").json()["error"]["code"] == "poll_not_found"
    assert vote(client, "nope1234", 0).json()["error"]["code"] == "poll_not_found"


def test_has_voted_tracks_voter_token(client, make_poll):
    poll = make_poll()
    url = f"/api/polls/{poll['poll_id']}"
    assert client.get(url, headers={"X-Voter-Token": VOTER_A}).json()["has_voted"] is False
    vote(client, poll["poll_id"], 0, voter=VOTER_A)
    assert client.get(url, headers={"X-Voter-Token": VOTER_A}).json()["has_voted"] is True
    assert client.get(url).json()["has_voted"] is False


def test_invalid_voter_token_is_rejected(client, make_poll):
    poll = make_poll()
    response = client.get(f"/api/polls/{poll['poll_id']}", headers={"X-Voter-Token": "short"})
    assert response.status_code == 422


def test_lifecycle_open_closed_deleted(client, make_poll, frozen_clock):
    poll = make_poll(expires_in_minutes=60)
    url = f"/api/polls/{poll['poll_id']}"
    vote(client, poll["poll_id"], 1)

    frozen_clock.advance(minutes=59)
    assert client.get(url).json()["status"] == "open"

    frozen_clock.advance(minutes=1)
    assert client.get(url).json()["status"] == "closed"
    assert client.get(f"{url}/results").json()["counts"] == [0, 1, 0]

    # Still readable through the grace period, gone (even before TTL deletion runs) after it.
    frozen_clock.advance(hours=24, minutes=-1)
    assert client.get(url).status_code == 200
    frozen_clock.advance(minutes=1)
    assert client.get(url).status_code == 404


def test_unknown_route_uses_error_shape(client):
    response = client.get("/api/nothing-here")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
