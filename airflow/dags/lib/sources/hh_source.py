from __future__ import annotations

import re
import time
from functools import lru_cache
from typing import Any
import logging
import httpx


BASE = "https://api.hh.ru"
logger = logging.getLogger(__name__)


def html_to_text(html: str | None) -> str | None:
    if not html:
        return None
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() or None


def _norm_city(value: str) -> str:
    return " ".join(value.strip().lower().replace("-", " ").split())


def _iter_areas(nodes: list[dict[str, Any]]):
    for node in nodes:
        yield node
        children = node.get("areas") or []
        if children:
            yield from _iter_areas(children)


@lru_cache(maxsize=1)
def _load_areas_tree(user_agent: str) -> list[dict[str, Any]]:
    with httpx.Client(
        base_url=BASE,
        timeout=30,
        headers={
            "User-Agent": user_agent,
            "HH-User-Agent": user_agent,
            "Accept": "application/json",
        },
    ) as client:
        response = client.get("/areas", params={"locale":"EN"})
        response.raise_for_status()
        return response.json()            


def resolve_area_id(city_name: str, user_agent: str, override_area_id: int | None = None) -> int:
    if override_area_id is not None:
        return int(override_area_id)

    normalized_city = _norm_city(city_name)
    areas = _load_areas_tree(user_agent)

    exact_match: int | None = None
    contains_match: int | None = None

    for node in _iter_areas(areas):
        name = node.get("name")
        area_id = node.get("id")
        if not name or area_id is None:
            continue

        normalized_name = _norm_city(name)

        if normalized_name == normalized_city:
            exact_match = int(area_id)
            break

        if normalized_city in normalized_name and contains_match is None:
            contains_match = int(area_id)

    if exact_match is not None:
        return exact_match
    if contains_match is not None:
        return contains_match

    return None


class HHApiClient:
    def __init__(
        self,
        user_agent: str,
        timeout: float = 25.0,
        min_delay: float = 0.4,
        max_delay: float = 0.9,
        max_retries: int = 3,
    ) -> None:
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.client = httpx.Client(
            base_url=BASE,
            timeout=timeout,
            headers={
                "User-Agent": user_agent,
                "HH-User-Agent": user_agent,
                "Accept": "application/json",
            },
        )


    def _sleep(self) -> None:
        time.sleep((self.min_delay + self.max_delay) / 2.0)
    

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_err: Exception | None = None
        last_text: str | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(path, params=params)
                if response.status_code >= 400:
                    last_text = response.text
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_err = exc
                time.sleep(0.8 * attempt)

        raise RuntimeError(
            f"GET failed: path={path} params={params} err={last_err} response_body={last_text}"
        )


    def search_vacancies(
        self,
        text: str,
        area: int,
        page: int = 0,
        per_page: int = 100,
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

        data = self._get("/vacancies", params=params)
        self._sleep()
        return data

    def get_vacancy(self, vacancy_id: str) -> dict[str, Any]:
        data = self._get(f"/vacancies/{vacancy_id}")
        self._sleep()
        return data


def map_hh_detail_to_record(detail: dict[str, Any]) -> dict[str, Any]:
    vacancy_id = str(detail.get("id"))
    url = detail.get("alternate_url") or detail.get("url") or f"{BASE}/vacancies/{vacancy_id}"

    employer = detail.get("employer") or {}
    company = employer.get("name")

    area = detail.get("area") or {}
    area_name = area.get("name")

    address = detail.get("address") or {}
    city = address.get("city")

    if city and area_name and city != area_name:
        location = f"{city}, {area_name}"
    else:
        location = area_name or city

    salary = detail.get("salary") or {}

    skills: list[str] = []
    for skill in detail.get("key_skills") or []:
        name = (skill or {}).get("name")
        if name:
            skills.append(name)

    return {
        "source": "hh",
        "external_id": vacancy_id,
        "title": detail.get("name"),
        "company": company,
        "location": location,
        "description": html_to_text(detail.get("description")),
        "url": url,
        "posted_at": detail.get("published_at"),
        "fetched_at": None,
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "currency": salary.get("currency"),
        "salary_text": None,
        "skills": skills,
        "raw_payload": detail,
    }


def collect_hh_vacancies(
    direction_name: str,
    city_name: str,
    user_agent: str,
    area_override: int | None = None,
    limit_total: int = 200,
    per_page: int = 100,
    max_pages: int = 10,
    only_with_salary: bool = False,
) -> list[dict[str, Any]]:
    area_id = resolve_area_id(
        city_name=city_name,
        user_agent=user_agent,
        override_area_id=area_override,
    )

    hh = HHApiClient(user_agent=user_agent)

    if area_id is None:
        logger.warning(
            "Skipping HH vacancies collection for city '%s' because area_id could not be resolved",
            city_name
        )
        return []

    out: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for page in range(max_pages):
        search = hh.search_vacancies(
            text=direction_name,
            area=area_id,
            page=page,
            per_page=per_page,
            only_with_salary=only_with_salary,
        )

        items = search.get("items") or []
        if not items:
            break

        for item in items:
            vacancy_id = str(item.get("id"))
            if not vacancy_id or vacancy_id in seen_ids:
                continue

            seen_ids.add(vacancy_id)

            try:
                detail = hh.get_vacancy(vacancy_id)
                out.append(map_hh_detail_to_record(detail))
            except Exception:
                continue

            if len(out) >= limit_total:
                return out

        pages = search.get("pages")
        if pages is not None and page >= int(pages) - 1:
            break

    return out