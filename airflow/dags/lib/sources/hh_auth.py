from __future__ import annotations

import os
from typing import Any

import httpx
from airflow.sdk import Variable

HH_API_BASE_URL = "https://api.hh.ru"
HH_OAUTH_BASE_URL = "https://hh.ru"

HH_CLIENT_ID = os.getenv("HH_CLIENT_ID")
HH_CLIENT_SECRET = os.getenv("HH_CLIENT_SECRET")

HH_APP_TOKEN_ENV = os.getenv("HH_APP_TOKEN")
HH_APP_TOKEN_VAR = "HH_APP_TOKEN"

# User/applicant OAuth tokens. Kept for future applicant-specific endpoints.
HH_USER_ACCESS_TOKEN_ENV = os.getenv("HH_USER_ACCESS_TOKEN") or os.getenv("HH_ACCESS_TOKEN")
HH_USER_REFRESH_TOKEN_ENV = os.getenv("HH_USER_REFRESH_TOKEN") or os.getenv("HH_REFRESH_TOKEN")
HH_USER_ACCESS_TOKEN_VAR = "HH_USER_ACCESS_TOKEN"
HH_USER_REFRESH_TOKEN_VAR = "HH_USER_REFRESH_TOKEN"

# Backward-compatible legacy Airflow Variable names.
LEGACY_HH_ACCESS_TOKEN_VAR = "HH_ACCESS_TOKEN"
LEGACY_HH_REFRESH_TOKEN_VAR = "HH_REFRESH_TOKEN"


class HHAuthError(RuntimeError):
    pass


def _get_variable(name: str) -> str | None:
    try:
        value = Variable.get(name, default=None)
    except Exception:
        value = None

    if value:
        value = str(value).strip()

    return value or None


def _set_variable(name: str, value: str) -> None:
    Variable.set(name, value)


def _auth_headers(access_token: str, user_agent: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "HH-User-Agent": user_agent,
        "Accept": "application/json",
    }


def inspect_hh_token(access_token: str, user_agent: str) -> dict[str, Any]:
    """Return /me payload for the provided HH access token."""
    response = httpx.get(
        f"{HH_API_BASE_URL}/me",
        headers=_auth_headers(access_token=access_token, user_agent=user_agent),
        timeout=20.0,
        follow_redirects=True,
    )

    if response.status_code >= 400:
        raise HHAuthError(
            "HH token inspection failed: "
            f"status={response.status_code}, body={response.text}"
        )

    payload = response.json()
    if not isinstance(payload, dict):
        raise HHAuthError(f"Unexpected HH /me response type: {type(payload)}")

    return payload


def is_application_token_payload(payload: dict[str, Any]) -> bool:
    return bool(payload.get("is_application") is True or payload.get("auth_type") == "application")


def get_hh_app_access_token() -> str:
    """
    Application/client token used for public vacancy collection:
    GET /vacancies and GET /vacancies/{id}.

    Do not put applicant/user OAuth token into HH_APP_TOKEN.
    """
    token = _get_variable(HH_APP_TOKEN_VAR) or HH_APP_TOKEN_ENV

    if token:
        token = str(token).strip()

    if not token:
        raise HHAuthError(
            "HH_APP_TOKEN is missing. Create an application token via HH developer cabinet "
            "and set it as Airflow Variable HH_APP_TOKEN or environment variable HH_APP_TOKEN."
        )

    return token


def verify_hh_app_access_token(access_token: str, user_agent: str) -> bool:
    try:
        payload = inspect_hh_token(access_token=access_token, user_agent=user_agent)
    except Exception:
        return False

    return is_application_token_payload(payload)


def ensure_hh_app_access_token(user_agent: str) -> str:
    token = get_hh_app_access_token()
    payload = inspect_hh_token(access_token=token, user_agent=user_agent)

    if not is_application_token_payload(payload):
        raise HHAuthError(
            "HH_APP_TOKEN is valid, but it is not an application token. "
            f"/me auth_type={payload.get('auth_type')!r}, "
            f"is_application={payload.get('is_application')!r}, "
            f"is_applicant={payload.get('is_applicant')!r}, "
            f"is_employer={payload.get('is_employer')!r}. "
            "Use an application/client token for vacancy collection."
        )

    return token


def get_current_hh_user_tokens() -> dict[str, str | None]:
    """
    User/applicant tokens are intentionally separate from HH_APP_TOKEN.
    Use them only for applicant-specific endpoints, not for vacancy collection.
    """
    access_token = (
        _get_variable(HH_USER_ACCESS_TOKEN_VAR)
        or _get_variable(LEGACY_HH_ACCESS_TOKEN_VAR)
        or HH_USER_ACCESS_TOKEN_ENV
    )
    refresh_token = (
        _get_variable(HH_USER_REFRESH_TOKEN_VAR)
        or _get_variable(LEGACY_HH_REFRESH_TOKEN_VAR)
        or HH_USER_REFRESH_TOKEN_ENV
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def verify_hh_user_access_token(access_token: str, user_agent: str) -> bool:
    try:
        payload = inspect_hh_token(access_token=access_token, user_agent=user_agent)
    except Exception:
        return False

    return bool(payload.get("is_applicant") or payload.get("is_employer") or payload.get("auth_type"))


def refresh_hh_user_access_token(refresh_token: str) -> dict[str, str]:
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
            f"HH user token refresh failed: status={response.status_code}, body={response.text}"
        )

    payload: dict[str, Any] = response.json()
    access_token = str(payload.get("access_token") or "").strip()
    new_refresh_token = str(payload.get("refresh_token") or "").strip()

    if not access_token or not new_refresh_token:
        raise HHAuthError(f"HH user token refresh returned incomplete payload: {payload}")

    _set_variable(HH_USER_ACCESS_TOKEN_VAR, access_token)
    _set_variable(HH_USER_REFRESH_TOKEN_VAR, new_refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
    }


def ensure_hh_user_access_token(user_agent: str) -> str:
    tokens = get_current_hh_user_tokens()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    if access_token and verify_hh_user_access_token(access_token, user_agent=user_agent):
        return access_token

    if refresh_token:
        refreshed = refresh_hh_user_access_token(refresh_token)
        return refreshed["access_token"]

    raise HHAuthError(
        "HH user OAuth token is missing. Initial OAuth authorization is required "
        "to obtain the first user access_token/refresh_token pair."
    )


# Backward-compatible alias. Do not use this for vacancy collection.
def ensure_hh_access_token(user_agent: str) -> str:
    return ensure_hh_user_access_token(user_agent=user_agent)