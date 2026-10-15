import pytest
from conftest import SETTINGS, VOTER_A, VOTER_B, vote
from fastapi.testclient import TestClient

from flashpoll.config import Settings
from flashpoll.main import create_app


def results(client, poll_id, voter=None):
    headers = {"X-Voter-Token": voter} if voter else {}
    return client.get(f"/api/polls/{poll_id}/results", headers=headers)


def test_vote_counts_and_returns_results(client, make_poll):
    poll = make_poll()
    assert vote(client, poll["poll_id"], 1).json() == {
        "results": {"total_votes": 1, "counts": [0, 1, 0]}
    }
    vote(client, poll["poll_id"], 1)
    vote(client, poll["poll_id"], 2)
    assert results(client, poll["poll_id"]).json() == {
        "status": "open",
        "total_votes": 3,
        "counts": [0, 2, 1],
    }


@pytest.mark.parametrize("option_index", [-1, 3])
def test_vote_rejects_bad_option(client, make_poll, option_index):
    poll = make_poll()
    response = vote(client, poll["poll_id"], option_index)
    assert response.status_code == 422
    assert results(client, poll["poll_id"]).json()["total_votes"] == 0


def test_vote_on_closed_poll(client, make_poll, frozen_clock):
    poll = make_poll(expires_in_minutes=15)
    frozen_clock.advance(minutes=15)
    response = vote(client, poll["poll_id"], 0)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "poll_closed"


def test_open_allows_repeat_votes(client, make_poll):
    poll = make_poll(vote_control="open")
    for _ in range(3):
        assert vote(client, poll["poll_id"], 0, voter=VOTER_A).status_code == 200
    assert results(client, poll["poll_id"]).json()["total_votes"] == 3


def test_one_per_browser(client, make_poll):
    poll = make_poll(vote_control="one_per_browser")
    assert vote(client, poll["poll_id"], 0, voter=VOTER_A).status_code == 200

    repeat = vote(client, poll["poll_id"], 1, voter=VOTER_A)
    assert repeat.status_code == 409
    assert repeat.json()["error"]["code"] == "already_voted"

    assert vote(client, poll["poll_id"], 1, voter=VOTER_B).status_code == 200
    # The rejected repeat vote was not counted.
    assert results(client, poll["poll_id"]).json()["counts"] == [1, 1, 0]


def test_one_per_browser_requires_voter_token(client, make_poll):
    poll = make_poll(vote_control="one_per_browser")
    response = vote(client, poll["poll_id"], 0)
    assert response.status_code == 422
    assert "X-Voter-Token" in response.json()["error"]["message"]


@pytest.fixture
def proxied_client(aws, frozen_clock):
    settings = Settings(**{**SETTINGS.__dict__, "client_ip_header": "CloudFront-Viewer-Address"})
    return TestClient(create_app(settings), raise_server_exceptions=False)


def test_one_per_ip(proxied_client, make_poll):
    client = proxied_client
    poll = make_poll(vote_control="one_per_ip")
    assert vote(client, poll["poll_id"], 0, voter=VOTER_A, ip="203.0.113.7").status_code == 200

    # A different browser on the same IP is still blocked.
    repeat = vote(client, poll["poll_id"], 1, voter=VOTER_B, ip="203.0.113.7")
    assert repeat.status_code == 409
    assert repeat.json()["error"]["code"] == "already_voted"

    assert vote(client, poll["poll_id"], 1, ip="198.51.100.2").status_code == 200
    assert results(client, poll["poll_id"]).json()["counts"] == [1, 1, 0]


def test_one_per_ip_ignores_x_forwarded_for(proxied_client, make_poll):
    client = proxied_client
    poll = make_poll(vote_control="one_per_ip")
    pid = poll["poll_id"]
    headers = {"CloudFront-Viewer-Address": "203.0.113.7:1111"}
    assert vote(client, pid, 0, ip="203.0.113.7").status_code == 200
    # A spoofed X-Forwarded-For changes nothing: only the CloudFront header counts.
    response = client.post(
        f"/api/polls/{pid}/votes",
        json={"option_index": 0},
        headers={**headers, "X-Forwarded-For": "9.9.9.9"},
    )
    assert response.status_code == 409


def test_raw_ip_and_voter_token_are_not_stored(proxied_client, make_poll, aws):
    poll = make_poll(vote_control="one_per_ip")
    vote(proxied_client, poll["poll_id"], 0, voter=VOTER_A, ip="203.0.113.7")
    items = aws.scan(TableName="flashpoll-votes")["Items"]
    assert len(items) == 2
    assert "203.0.113.7" not in str(items)
    assert VOTER_A not in str(items)


class TestResultsVisibility:
    def test_live(self, client, make_poll):
        poll = make_poll(results_visibility="live")
        assert results(client, poll["poll_id"]).status_code == 200

    def test_after_voting(self, client, make_poll, frozen_clock):
        poll = make_poll(results_visibility="after_voting", expires_in_minutes=60)
        pid = poll["poll_id"]

        hidden = results(client, pid, voter=VOTER_A)
        assert hidden.status_code == 403
        assert hidden.json()["error"]["code"] == "results_hidden"
        assert client.get(f"/api/polls/{pid}").json()["results_available"] is False

        assert vote(client, pid, 0, voter=VOTER_A).json()["results"]["counts"] == [1, 0, 0]
        assert results(client, pid, voter=VOTER_A).status_code == 200
        view = client.get(f"/api/polls/{pid}", headers={"X-Voter-Token": VOTER_A}).json()
        assert view["results_available"] is True
        assert results(client, pid, voter=VOTER_B).status_code == 403

        frozen_clock.advance(minutes=60)
        assert results(client, pid).status_code == 200

    def test_after_voting_without_voter_token_gets_no_results(self, client, make_poll):
        poll = make_poll(results_visibility="after_voting", vote_control="open")
        assert vote(client, poll["poll_id"], 0).json() == {"results": None}

    def test_private(self, client, make_poll, frozen_clock):
        poll = make_poll(results_visibility="private", expires_in_minutes=60)
        pid = poll["poll_id"]
        assert vote(client, pid, 0, voter=VOTER_A).json() == {"results": None}
        assert results(client, pid, voter=VOTER_A).status_code == 403
        frozen_clock.advance(minutes=60)
        assert results(client, pid, voter=VOTER_A).status_code == 403
