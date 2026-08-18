import ipaddress
import os
from functools import wraps
from urllib.parse import urlparse


_TRUTHY = {"1", "true", "yes", "on", "si"}
_DEFAULT_NEWS_HOSTS = {"www.infobae.com", "infobae.com"}


class OutboundNetworkBlocked(RuntimeError):
    """Se lanza cuando una salida externa no está permitida por configuración."""


def _env_flag(name: str, default=False) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return str(raw_value).strip().lower() in _TRUTHY


def allow_external_network() -> bool:
    return _env_flag("ALLOW_EXTERNAL_NETWORK", default=False)


def allow_external_news() -> bool:
    return _env_flag("ALLOW_EXTERNAL_NEWS", default=False)


def allow_external_ai() -> bool:
    return _env_flag("ALLOW_EXTERNAL_AI", default=False)


def local_voice_enabled() -> bool:
    return _env_flag("ENABLE_LOCAL_VOICE", default=True)


def local_audio_upload_enabled() -> bool:
    return _env_flag("ENABLE_LOCAL_AUDIO_UPLOAD", default=False)


def enforce_browser_local_only() -> bool:
    return _env_flag("ENFORCE_BROWSER_LOCAL_ONLY", default=True)


def allowed_external_hosts() -> set[str]:
    raw_value = os.environ.get("ALLOWED_EXTERNAL_HOSTS", "").strip()
    hosts = {host.strip().lower() for host in raw_value.split(",") if host.strip()}
    if allow_external_news():
        hosts.update(_DEFAULT_NEWS_HOSTS)
    return hosts


def _is_private_ip(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def is_local_or_private_host(hostname: str) -> bool:
    normalized = (hostname or "").strip().lower()
    if not normalized:
        return True
    if normalized in {"localhost", "127.0.0.1", "::1"}:
        return True
    if normalized.endswith(".local") or normalized.endswith(".lan"):
        return True
    return _is_private_ip(normalized)


def is_outbound_url_allowed(url: str, purpose="general") -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").strip().lower()

    if parsed.scheme not in {"http", "https"}:
        return True
    if is_local_or_private_host(hostname):
        return True
    if purpose == "news" and allow_external_news() and hostname in _DEFAULT_NEWS_HOSTS:
        return True
    if allow_external_network():
        allowlist = allowed_external_hosts()
        return not allowlist or hostname in allowlist
    return False


def guard_outbound_url(url: str, purpose="general") -> None:
    if is_outbound_url_allowed(url, purpose=purpose):
        return
    raise OutboundNetworkBlocked(
        f"Salida externa bloqueada por configuración para {url}. "
        f"Purpose={purpose}. Ajuste ALLOW_EXTERNAL_NEWS/ALLOW_EXTERNAL_NETWORK si corresponde."
    )


def _wrap_http_request(method, *, url_index: int):
    if getattr(method, "_inventario_network_guard", False):
        return method

    @wraps(method)
    def guarded(*args, **kwargs):
        url = kwargs.get("url")
        if url is None and len(args) > url_index:
            url = args[url_index]
        if url:
            guard_outbound_url(str(url))
        return method(*args, **kwargs)

    guarded._inventario_network_guard = True
    return guarded


def install_outbound_guards() -> None:
    try:
        import requests.sessions

        requests.sessions.Session.request = _wrap_http_request(
            requests.sessions.Session.request,
            url_index=2,
        )
    except Exception:
        pass

    try:
        import httpx

        httpx.Client.request = _wrap_http_request(httpx.Client.request, url_index=2)
        httpx.AsyncClient.request = _wrap_http_request(httpx.AsyncClient.request, url_index=2)
    except Exception:
        pass
