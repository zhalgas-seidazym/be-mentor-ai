from __future__ import annotations

import logging
import os
import random
import time
from typing import Any

import httpx

from lib.sources.hh_auth import HHAuthError, get_hh_app_access_token

logger = logging.getLogger(__name__)

HH_BASE_URL = "https://api.hh.ru"
HH_REQUEST_DELAY_SECONDS = float(os.getenv("HH_REQUEST_DELAY_SECONDS", "1.2"))
HH_DETAIL_DELAY_SECONDS = float(os.getenv("HH_DETAIL_DELAY_SECONDS", "0.8"))
HH_AREAS_CACHE_TTL_SECONDS = int(os.getenv("HH_AREAS_CACHE_TTL_SECONDS", "86400"))


class HHForbiddenError(RuntimeError):
    pass


class HHCaptchaRequiredError(RuntimeError):
    pass


class HHApiClient:
    def __init__(
        self,
        user_agent: str,
        access_token: str | None = None,
        max_retries: int = 3,
    ) -> None:
        if not user_agent or "your_email@example.com" in user_agent:
            raise ValueError(
                "MENTORAI_HH_USER_AGENT must contain a real contact email, "
                "not the placeholder value."
            )

        self.user_agent = user_agent
        self.access_token = access_token
        self.max_retries = max_retries

        headers = {
            "User-Agent": user_agent,
            "HH-User-Agent": user_agent,
            "Accept": "application/json",
        }

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        self.client = httpx.Client(
            base_url=HH_BASE_URL,
            timeout=30.0,
            follow_redirects=True,
            headers=headers,
        )

    def _sleep(self, base_delay: float) -> None:
        jitter = random.uniform(0.0, 0.35)
        time.sleep(base_delay + jitter)

    def _raise_hh_error(
        self,
        response: httpx.Response,
        path: str,
        params: dict[str, Any] | None,
    ) -> None:
        request_id = response.headers.get("x-request-id")

        try:
            payload = response.json()
        except Exception:
            payload = {}

        if isinstance(payload, dict):
            request_id = request_id or payload.get("request_id")
            errors = payload.get("errors") or []
        else:
            errors = []

        first_error = errors[0] if errors and isinstance(errors[0], dict) else {}
        error_type = first_error.get("type")
        error_value = first_error.get("value")

        message = (
            "HH API error: "
            f"status={response.status_code}, path={path}, params={params}, "
            f"request_id={request_id}, error_type={error_type}, "
            f"error_value={error_value}, response_body={response.text}"
        )

        logger.error(message)

        if error_type == "captcha_required":
            raise HHCaptchaRequiredError(message)

        if error_type == "oauth" or response.status_code == 401:
            raise HHAuthError(message)

        if response.status_code == 403:
            raise HHForbiddenError(message)

        raise RuntimeError(message)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_err: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(path, params=params)

                if response.status_code >= 400:
                    self._raise_hh_error(response=response, path=path, params=params)

                payload = response.json()
                if not isinstance(payload, dict):
                    raise RuntimeError(
                        f"Unexpected HH response type for path={path}: {type(payload)}"
                    )

                return payload

            except (HHAuthError, HHForbiddenError, HHCaptchaRequiredError):
                raise
            except httpx.RequestError as exc:
                last_err = exc
            except RuntimeError as exc:
                last_err = exc
                break
            except Exception as exc:
                last_err = exc

            self._sleep(0.8 * attempt)

        raise RuntimeError(f"GET failed: path={path} params={params} err={last_err}")

    def get_areas(self, locale: str = "EN") -> list[dict[str, Any]]:
        response = self.client.get("/areas", params={"locale": locale})

        if response.status_code >= 400:
            self._raise_hh_error(response=response, path="/areas", params={"locale": locale})

        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected /areas response type: {type(data)}")

        return data

    def search_vacancies(
        self,
        text: str,
        area: int,
        page: int,
        per_page: int,
        only_with_salary: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "text": text,
            "area": area,
            "page": page,
            "per_page": per_page,
        }

        if only_with_salary:
            params["only_with_salary"] = True

        self._sleep(HH_REQUEST_DELAY_SECONDS)
        return self._get("/vacancies", params=params)

    def get_vacancy(self, vacancy_id: str) -> dict[str, Any]:
        self._sleep(HH_DETAIL_DELAY_SECONDS)
        return self._get(f"/vacancies/{vacancy_id}")


_AREAS_CACHE: dict[str, Any] = {
    "fetched_at": 0.0,
    "areas": None,
}


def _walk_areas(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def dfs(items: list[dict[str, Any]]) -> None:
        for item in items:
            result.append(item)
            children = item.get("areas") or []
            if children:
                dfs(children)

    dfs(nodes)
    return result


def _load_areas_cached(client: HHApiClient, locale: str = "EN") -> list[dict[str, Any]]:
    now_ts = time.time()
    cached = _AREAS_CACHE.get("areas")
    fetched_at = float(_AREAS_CACHE.get("fetched_at") or 0.0)

    if cached and now_ts - fetched_at < HH_AREAS_CACHE_TTL_SECONDS:
        return cached

    areas = client.get_areas(locale=locale)
    flattened = _walk_areas(areas)

    _AREAS_CACHE["areas"] = flattened
    _AREAS_CACHE["fetched_at"] = now_ts

    return flattened


def _resolve_area_id_by_city_name(
    client: HHApiClient,
    city_name: str,
) -> int | None:
    city_name_norm = city_name.strip().lower()
    areas = _load_areas_cached(client=client, locale="EN")

    for area in areas:
        name = str(area.get("name") or "").strip().lower()
        if name == city_name_norm:
            return int(area["id"])

    return None


def _extract_salary_amount_and_currency(vacancy: dict[str, Any]) -> tuple[float | None, str | None]:
    salary = vacancy.get("salary")
    if not salary:
        return None, None

    salary_from = salary.get("from")
    salary_to = salary.get("to")
    currency = salary.get("currency")

    if salary_from is not None and salary_to is not None:
        return float(salary_from + salary_to) / 2.0, currency

    if salary_from is not None:
        return float(salary_from), currency

    if salary_to is not None:
        return float(salary_to), currency

    return None, currency


def _extract_skills_from_vacancy_detail(vacancy_detail: dict[str, Any]) -> list[str]:
    skills = vacancy_detail.get("key_skills") or []
    result: list[str] = []

    for skill in skills:
        name = str(skill.get("name") or "").strip()
        if name:
            result.append(name)

    return result


def extract_job_from_detail(vacancy_detail: dict[str, Any]) -> dict[str, Any]:
    salary_amount, salary_currency = _extract_salary_amount_and_currency(vacancy_detail)

    return {
        "source": "hh",
        "external_id": str(vacancy_detail.get("id") or ""),
        "title": vacancy_detail.get("name"),
        "url": vacancy_detail.get("alternate_url"),
        "description": (vacancy_detail.get("description") or "")[:10000],
        "salary_amount": salary_amount,
        "currency": salary_currency,
        "skills": _extract_skills_from_vacancy_detail(vacancy_detail),
    }


def collect_hh_vacancies(
    direction_name: str,
    city_name: str,
    user_agent: str,
    app_access_token: str | None = None,
    area_override: int | None = None,
    limit_total: int = 60,
    per_page: int = 30,
    max_pages: int = 3,
    only_with_salary: bool = False,
) -> list[dict[str, Any]]:
    access_token = app_access_token or get_hh_app_access_token()

    hh = HHApiClient(
        user_agent=user_agent,
        access_token=access_token,
    )

    area_id = area_override
    if area_id is None:
        area_id = _resolve_area_id_by_city_name(
            client=hh,
            city_name=city_name,
        )

    if area_id is None:
        raise RuntimeError(
            "HH area id was not resolved. "
            f"city_name={city_name!r}, direction_name={direction_name!r}. "
            "Set HH_AREA_OVERRIDES_JSON or store HH area id for this city."
        )

    jobs: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for page in range(max_pages):
        search = hh.search_vacancies(
            text=direction_name,
            area=int(area_id),
            page=page,
            per_page=per_page,
            only_with_salary=only_with_salary,
        )

        items = search.get("items") or []
        if not items:
            break

        for item in items:
            vacancy_id = str(item.get("id") or "")

            if not vacancy_id or vacancy_id in seen_ids:
                continue

            seen_ids.add(vacancy_id)

            try:
                detail = hh.get_vacancy(vacancy_id)
                jobs.append(extract_job_from_detail(detail))
            except (HHAuthError, HHForbiddenError, HHCaptchaRequiredError):
                raise
            except Exception as exc:
                logger.warning(
                    "Skipping HH vacancy detail: vacancy_id=%s err=%s",
                    vacancy_id,
                    exc,
                )
                continue

            if len(jobs) >= limit_total:
                break

        if len(jobs) >= limit_total:
            break

        pages_total = search.get("pages")
        if pages_total is not None and page >= int(pages_total) - 1:
            break

    return jobs