from conftest import VOTER_A, admin_headers, vote


def test_admin_requires_valid_token(client, make_poll):
    make_poll()
    for headers in ({}, admin_headers("not-a-real-token"), {"Authorization": "Basic abc"}):
        response = client.get("/api/admin/poll", headers=headers)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"
    assert client.post("/api/admin/poll/close").status_code == 401
    assert client.delete("/api/admin/poll").status_code == 401


def test_admin_view_includes_results_even_when_private(client, make_poll):
    poll = make_poll(results_visibility="private")
    vote(client, poll["poll_id"], 2, voter=VOTER_A)
    response = client.get("/api/admin/poll", headers=admin_headers(poll["admin_token"]))
    assert response.status_code == 200
    body = response.json()
    assert body["poll_id"] == poll["poll_id"]
    assert body["results"] == {"total_votes": 1, "counts": [0, 0, 1]}
    assert body["deletes_at"] == "2027-01-16T09:00:00Z"


def test_admin_close(client, make_poll, frozen_clock):
    poll = make_poll(expires_in_minutes=60)
    headers = admin_headers(poll["admin_token"])
    frozen_clock.advance(minutes=10)

    closed = client.post("/api/admin/poll/close", headers=headers).json()
    assert closed["status"] == "closed"
    assert closed["expires_at"] == "2027-01-15T08:10:00Z"
    # Deletion time is unchanged by closing early.
    assert closed["deletes_at"] == "2027-01-16T09:00:00Z"
    assert vote(client, poll["poll_id"], 0).json()["error"]["code"] == "poll_closed"

    # Idempotent: closing again doesn't move expires_at.
    frozen_clock.advance(minutes=5)
    again = client.post("/api/admin/poll/close", headers=headers).json()
    assert again["expires_at"] == "2027-01-15T08:10:00Z"


def test_admin_delete_removes_poll_and_votes(client, make_poll, aws):
    poll = make_poll(vote_control="one_per_browser")
    other = make_poll(vote_control="one_per_browser")
    vote(client, poll["poll_id"], 0, voter=VOTER_A)
    vote(client, other["poll_id"], 0, voter=VOTER_A)

    response = client.delete("/api/admin/poll", headers=admin_headers(poll["admin_token"]))
    assert response.status_code == 204
    assert client.get(f"/api/polls/{poll['poll_id']}").status_code == 404
    assert (
        client.get("/api/admin/poll", headers=admin_headers(poll["admin_token"])).status_code == 401
    )

    remaining = aws.scan(TableName="flashpoll-votes")["Items"]
    assert [item["poll_id"]["S"] for item in remaining] == [other["poll_id"]]


def test_admin_token_for_one_poll_cannot_touch_another(client, make_poll):
    first = make_poll()
    second = make_poll()
    body = client.get("/api/admin/poll", headers=admin_headers(first["admin_token"])).json()
    assert body["poll_id"] == first["poll_id"] != second["poll_id"]
