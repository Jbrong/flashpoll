from types import SimpleNamespace

from flashpoll.security import client_ip, voter_key


def request(peer="10.0.0.1", forwarded=None):
    headers = {"x-forwarded-for": forwarded} if forwarded else {}
    return SimpleNamespace(client=SimpleNamespace(host=peer), headers=headers)


def test_client_ip_uses_peer_when_no_proxies_trusted():
    assert client_ip(request(forwarded="1.2.3.4"), 0) == "10.0.0.1"


def test_client_ip_takes_nth_from_right():
    req = request(forwarded="6.6.6.6, 1.2.3.4, 130.176.0.1")
    assert client_ip(req, 1) == "130.176.0.1"
    assert client_ip(req, 2) == "1.2.3.4"


def test_client_ip_falls_back_when_header_too_short():
    assert client_ip(request(forwarded="1.2.3.4"), 2) == "10.0.0.1"


def test_voter_key_is_per_poll():
    assert voter_key("ip", "poll1", "1.2.3.4") != voter_key("ip", "poll2", "1.2.3.4")
    assert voter_key("ip", "poll1", "1.2.3.4").startswith("ip#")
