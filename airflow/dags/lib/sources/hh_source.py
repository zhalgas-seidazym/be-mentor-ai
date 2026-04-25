from __future__ import annotations

import logging
import os
import random
import time
from typing import Any

import httpx
from lib.sources.hh_auth import ensure_hh_access_token, HHAuthError




logger = logging.getLogger(__name__)

HH_BASE_URL = "https://api.hh.ru"
HH_REQUEST_DELAY_SECONDS = float(os.getenv("HH_REQUEST_DELAY_SECONDS", "1.2"))
HH_DETAIL_DELAY_SECONDS = float(os.getenv("HH_DETAIL_DELAY_SECONDS", "0.8"))


class HHForbiddenError(RuntimeError):
    pass


class HHApiClient:
    def __init__(
        self,
        user_agent: str,
        access_token: str | None = None,
        max_retries: int = 3,
    ) -> None:
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

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_err: Exception | None = None
        last_text: str | None = None
        last_status_code: int | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(path, params=params)
                last_status_code = response.status_code

                if response.status_code >= 400:
                    last_text = response.text

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as exc:
                last_err = exc
                last_status_code = exc.response.status_code
                last_text = exc.response.text

                if exc.response.status_code == 403:
                    raise HHForbiddenError(
                        f"HH returned 403 Forbidden: path={path} params={params} response_body={last_text}"
                    ) from exc

                # 4xx кроме 403 не ретраим много раз
                if 400 <= exc.response.status_code < 500:
                    break

            except Exception as exc:
                last_err = exc

            self._sleep(0.8 * attempt)

        raise RuntimeError(
            f"GET failed: path={path} params={params} err={last_err} "
            f"response_body={last_text} status_code={last_status_code}"
        )

    def get_areas(self, locale: str = "EN") -> list[dict[str, Any]]:
        data = self._get("/areas", params={"locale": locale})
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
HH_AREAS_CACHE_TTL_SECONDS = int(os.getenv("HH_AREAS_CACHE_TTL_SECONDS", "86400"))


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
    area_override: int | None = None,
    limit_total: int = 60,
    per_page: int = 30,
    max_pages: int = 3,
    only_with_salary: bool = False,
) -> list[dict[str, Any]]:
    
    try:
        access_token = ensure_hh_access_token(user_agent=user_agent)
    except HHAuthError as e:
        logger.warning("Skipping HH vacancy collection due to auth problem: %s", e)
        return []

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
        logger.warning(
            "Skipping HH vacancy collection because city was not found in HH areas: city_name=%s, direction_name=%s",
            city_name,
            direction_name,
        )
        return []

    jobs: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for page in range(max_pages):
        try:
            search = hh.search_vacancies(
                text=direction_name,
                area=area_id,
                page=page,
                per_page=per_page,
                only_with_salary=only_with_salary,
            )
        except HHForbiddenError as e:
            logger.warning(
                "Skipping HH vacancy collection due to 403 Forbidden: city_name=%s, direction_name=%s, area_id=%s, err=%s",
                city_name,
                direction_name,
                area_id,
                e,
            )
            return []

        items = search.get("items") or []
        if not items:
            break

        for item in items:
            vacancy_id = str(item.get("id") or "")
            if not vacancy_id or vacancy_id in seen_ids:
                continue
            seen_ids.add(vacancy_id)

            # Не валим target, если detail конкретной вакансии недоступен
            try:
                detail = hh.get_vacancy(vacancy_id)
                jobs.append(extract_job_from_detail(detail))
            except HHForbiddenError as e:
                logger.warning(
                    "Skipping HH vacancy detail due to 403 Forbidden: vacancy_id=%s, err=%s",
                    vacancy_id,
                    e,
                )
                continue
            except Exception as e:
                logger.warning(
                    "Skipping HH vacancy detail: vacancy_id=%s err=%s",
                    vacancy_id,
                    e,
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