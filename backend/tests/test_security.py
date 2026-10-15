from types import SimpleNamespace

from conftest import SETTINGS
from fastapi.testclient import TestClient

from flashpoll.config import Settings
from flashpoll.main import create_app
from flashpoll.security import client_ip, origin_verified, voter_key

HEADER = "CloudFront-Viewer-Address"


def request(peer="10.0.0.1", headers=None):
    return SimpleNamespace(client=SimpleNamespace(host=peer), headers=headers or {})


def test_client_ip_uses_peer_without_a_header_setting():
    assert client_ip(request(headers={HEADER: "1.2.3.4:5"}), None) == "10.0.0.1"


def test_client_ip_reads_viewer_address_and_strips_port():
    assert client_ip(request(headers={HEADER: "203.0.113.7:46532"}), HEADER) == "203.0.113.7"
    assert client_ip(request(headers={HEADER: "2001:db8::1:46532"}), HEADER) == "2001:db8::1"


def test_client_ip_falls_back_to_peer_when_header_missing():
    assert client_ip(request(), HEADER) == "10.0.0.1"


def test_voter_key_is_per_poll():
    assert voter_key("ip", "poll1", "1.2.3.4") != voter_key("ip", "poll2", "1.2.3.4")
    assert voter_key("ip", "poll1", "1.2.3.4").startswith("ip#")


def test_origin_verified():
    assert origin_verified(None, None)
    assert origin_verified("anything", None)
    assert origin_verified("s3cret", "s3cret")
    assert not origin_verified(None, "s3cret")
    assert not origin_verified("wrong", "s3cret")


def test_origin_secret_is_enforced(aws, frozen_clock):
    settings = Settings(**{**SETTINGS.__dict__, "origin_verify_secret": "s3cret"})
    client = TestClient(create_app(settings), raise_server_exceptions=False)

    blocked = client.get("/api/health")
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "forbidden"
    assert client.get("/api/health", headers={"X-Origin-Verify": "wrong"}).status_code == 403
    assert client.get("/api/health", headers={"X-Origin-Verify": "s3cret"}).status_code == 200
