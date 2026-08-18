import os

from flask import request


def _normalize_url(url):
    return (url or "").strip().rstrip("/")


def _request_origin():
    forwarded_proto = (request.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip()
    forwarded_host = (request.headers.get("X-Forwarded-Host") or "").split(",")[0].strip()
    scheme = forwarded_proto or request.scheme or "http"
    host = forwarded_host or request.host
    return f"{scheme}://{host}".rstrip("/")


def get_public_app_base_url():
    configured = _normalize_url(os.environ.get("INVENTARIO_PUBLIC_BASE_URL", ""))
    if configured:
        return configured

    return _request_origin()


def get_public_script_fallback_url():
    configured = _normalize_url(os.environ.get("INVENTARIO_PUBLIC_HTTP_FALLBACK_URL", ""))
    if configured:
        return configured

    current_host = request.host.split(":")[0]
    return f"http://{current_host}:8080"
