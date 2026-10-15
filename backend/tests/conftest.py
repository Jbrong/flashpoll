import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from flashpoll import clock
from flashpoll.config import Settings
from flashpoll.main import create_app
from flashpoll.tables import create_tables

SETTINGS = Settings(app_url="https://flashpoll.test", cors_origins=[])
START = 1_800_000_000

VOTER_A = "voter-token-aaaaaaaa"
VOTER_B = "voter-token-bbbbbbbb"


@pytest.fixture(autouse=True)
def aws(monkeypatch):
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(name, "testing")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with mock_aws():
        client = boto3.client("dynamodb", region_name=SETTINGS.aws_region)
        create_tables(client, SETTINGS.polls_table, SETTINGS.votes_table)
        yield client


class Clock:
    def __init__(self, monkeypatch):
        self.time = START
        monkeypatch.setattr(clock, "now", lambda: self.time)

    def advance(self, *, minutes: int = 0, hours: int = 0) -> None:
        self.time += minutes * 60 + hours * 3600


@pytest.fixture
def frozen_clock(monkeypatch) -> Clock:
    return Clock(monkeypatch)


@pytest.fixture
def client(aws, frozen_clock) -> TestClient:
    return TestClient(create_app(SETTINGS), raise_server_exceptions=False)


@pytest.fixture
def make_poll(client):
    def make(**overrides) -> dict:
        body = {
            "question": "Lunch?",
            "options": ["Pizza", "Tacos", "Salad"],
            "expires_in_minutes": 60,
            "vote_control": "open",
            "results_visibility": "live",
            **overrides,
        }
        response = client.post("/api/polls", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return make


def vote(client, poll_id: str, option_index: int, voter: str | None = None, ip: str | None = None):
    headers = {}
    if voter:
        headers["X-Voter-Token"] = voter
    if ip:
        headers["CloudFront-Viewer-Address"] = f"{ip}:4567"
    return client.post(
        f"/api/polls/{poll_id}/votes", json={"option_index": option_index}, headers=headers
    )


def admin_headers(token: str) -> dict:
    return {"X-Admin-Token": token}
