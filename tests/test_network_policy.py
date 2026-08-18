import pytest

from utils.network_policy import OutboundNetworkBlocked, guard_outbound_url, is_outbound_url_allowed


def test_private_hosts_remain_allowed(monkeypatch):
    monkeypatch.delenv("ALLOW_EXTERNAL_NETWORK", raising=False)
    monkeypatch.delenv("ALLOW_EXTERNAL_NEWS", raising=False)

    assert is_outbound_url_allowed("http://127.0.0.1:5000/api/ping")
    assert is_outbound_url_allowed("http://10.15.2.251:5000/mobile")


def test_external_news_is_blocked_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_EXTERNAL_NETWORK", raising=False)
    monkeypatch.delenv("ALLOW_EXTERNAL_NEWS", raising=False)

    with pytest.raises(OutboundNetworkBlocked):
        guard_outbound_url("https://www.infobae.com/arc/outboundfeeds/rss/", purpose="news")


def test_external_news_can_be_enabled_explicitly(monkeypatch):
    monkeypatch.delenv("ALLOW_EXTERNAL_NETWORK", raising=False)
    monkeypatch.setenv("ALLOW_EXTERNAL_NEWS", "true")

    guard_outbound_url("https://www.infobae.com/arc/outboundfeeds/rss/", purpose="news")

