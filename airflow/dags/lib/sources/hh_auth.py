from __future__ import annotations

import os
from typing import Any

import httpx
from airflow.sdk import Variable


HH_OAUTH_BASE_URL = "https://hh.ru"
HH_API_BASE_URL = "https://api.hh.ru"

HH_CLIENT_ID = os.getenv("HH_CLIENT_ID")
HH_CLIENT_SECRET = os.getenv("HH_CLIENT_SECRET")

HH_ACCESS_TOKEN_ENV = os.getenv("HH_ACCESS_TOKEN")
HH_REFRESH_TOKEN_ENV = os.getenv("HH_REFRESH_TOKEN")

HH_ACCESS_TOKEN_VAR = "HH_ACCESS_TOKEN"
HH_REFRESH_TOKEN_VAR = "HH_REFRESH_TOKEN"


class HHAuthError(RuntimeError):
    pass


def _get_variable(name: str) -> str | None:
    value = Variable.get(name, default=None)
    if value:
        value = str(value).strip()
    return value or None


def _set_variable(name: str, value: str) -> None:
    Variable.set(name, value)


def get_current_hh_tokens() -> dict[str, str | None]:
    access_token = _get_variable(HH_ACCESS_TOKEN_VAR) or HH_ACCESS_TOKEN_ENV
    refresh_token = _get_variable(HH_REFRESH_TOKEN_VAR) or HH_REFRESH_TOKEN_ENV

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def verify_access_token(access_token: str, user_agent: str) -> bool:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "HH-User-Agent": user_agent,
        "Accept": "application/json",
    }

    try:
        response = httpx.get(
            f"{HH_API_BASE_URL}/me",
            headers=headers,
            timeout=20.0,
            follow_redirects=True,
        )
        return response.status_code == 200
    except Exception:
        return False


def refresh_access_token(refresh_token: str) -> dict[str, str]:
    if not HH_CLIENT_ID or not HH_CLIENT_SECRET:
        raise HHAuthError("HH_CLIENT_ID / HH_CLIENT_SECRET are not configured")

    response = httpx.post(
        f"{HH_OAUTH_BASE_URL}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": HH_CLIENT_ID,
            "client_secret": HH_CLIENT_SECRET,
        },
        headers={"Accept": "application/json"},
        timeout=30.0,
        follow_redirects=True,
    )

    if response.status_code >= 400:
        raise HHAuthError(
            f"HH token refresh failed: status={response.status_code}, body={response.text}"
        )

    payload: dict[str, Any] = response.json()
    access_token = str(payload.get("access_token") or "").strip()
    new_refresh_token = str(payload.get("refresh_token") or "").strip()

    if not access_token or not new_refresh_token:
        raise HHAuthError(f"HH token refresh returned incomplete payload: {payload}")

    _set_variable(HH_ACCESS_TOKEN_VAR, access_token)
    _set_variable(HH_REFRESH_TOKEN_VAR, new_refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
    }


def ensure_hh_access_token(user_agent: str) -> str:
    tokens = get_current_hh_tokens()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    if access_token and verify_access_token(access_token, user_agent=user_agent):
        return access_token

    if refresh_token:
        refreshed = refresh_access_token(refresh_token)
        return refreshed["access_token"]

    raise HHAuthError(
        "HH token is missing. Initial OAuth authorization is required to obtain the first access_token/refresh_token pair."
    )