from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def norm_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize_skill_name(skill: str) -> str:
    s = norm_text(skill).lower()
    s = s.replace("c ++", "c++").replace("node js", "node.js")
    return s


def uniq_keep_order(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = norm_text(value)
        key = normalize_skill_name(cleaned)
        if not cleaned or not key or key in seen:
            continue
        seen.add(key)
        out.append(cleaned)

    return out


_MONEY_RE = re.compile(
    r"(?P<cur1>\$|€|₸|£|USD|EUR|KZT|RUB|RUR|GBP)?\s*"
    r"(?P<a>\d[\d,\s]{2,})"
    r"(?:\s*[-–]\s*"
    r"(?P<cur2>\$|€|₸|£|USD|EUR|KZT|RUB|RUR|GBP)?\s*"
    r"(?P<b>\d[\d,\s]{2,}))?",
    re.IGNORECASE,
)


def _clean_amount(raw: str | None) -> float | None:
    if not raw:
        return None
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return None
    try:
        return float(digits)
    except Exception:
        return None


def _normalize_currency(cur: str | None) -> str | None:
    if not cur:
        return None
    c = cur.strip().upper()
    mapping = {
        "$": "USD",
        "€": "EUR",
        "₸": "KZT",
        "£": "GBP",
        "RUR": "RUB",
    }
    return mapping.get(c, c)


def parse_salary_text(text: str | None) -> tuple[float | None, float | None, str | None]:
    if not text:
        return None, None, None

    match = _MONEY_RE.search(text)
    if not match:
        return None, None, None

    salary_from = _clean_amount(match.group("a"))
    salary_to = _clean_amount(match.group("b"))
    currency = _normalize_currency(match.group("cur1") or match.group("cur2"))

    return salary_from, salary_to, currency


def extract_known_skills_from_text(text: str, known_skill_names: list[str]) -> list[str]:
    text_l = f" {norm_text(text).lower()} "
    found: list[str] = []

    for skill in known_skill_names:
        normalized = normalize_skill_name(skill)
        if not normalized:
            continue

        token = f" {normalized} "
        if token in text_l:
            found.append(skill)
            continue

        if normalized in {"c++", "c#", ".net", "node.js", "react.js", "next.js"}:
            if normalized in text_l:
                found.append(skill)

    return uniq_keep_order(found)


def build_source_key(v: dict[str, Any]) -> str:
    source = norm_text(v.get("source")).lower()
    external_id = norm_text(v.get("external_id"))
    url = norm_text(v.get("url"))
    title = norm_text(v.get("title")).lower()

    if external_id:
        return f"{source}::{external_id}"
    if url:
        return f"{source}::{url}"
    return f"{source}::{title}"


def finalize_vacancy_record(
    raw: dict[str, Any],
    target: dict[str, Any],
    known_skill_names: list[str] | None = None,
) -> dict[str, Any]:
    title = norm_text(raw.get("title"))
    url = norm_text(raw.get("url"))
    description = norm_text(raw.get("description"))

    salary_from = raw.get("salary_from")
    salary_to = raw.get("salary_to")
    currency = raw.get("currency")

    if salary_from is None and salary_to is None:
        parsed_from, parsed_to, parsed_currency = parse_salary_text(
            raw.get("salary_text") or description
        )
        salary_from = salary_from or parsed_from
        salary_to = salary_to or parsed_to
        currency = currency or parsed_currency

    salary_amount = None
    if salary_from is not None and salary_to is not None:
        salary_amount = (salary_from + salary_to) / 2
    elif salary_from is not None:
        salary_amount = salary_from
    elif salary_to is not None:
        salary_amount = salary_to

    source_skills = uniq_keep_order(raw.get("skills") or [])
    inferred_skills: list[str] = []

    if known_skill_names:
        combined_text = f"{title}\n{description}".strip()
        if combined_text:
            inferred_skills = extract_known_skills_from_text(combined_text, known_skill_names)

    skills = uniq_keep_order(source_skills + inferred_skills)

    record = {
        "source": norm_text(raw.get("source")) or "unknown",
        "external_id": norm_text(raw.get("external_id")) or None,
        "direction_id": int(target["direction_id"]),
        "city_id": int(target["city_id"]),
        "title": title or None,
        "salary_amount": salary_amount,
        "salary_currency": currency,
        "vacancy_type": "OFFLINE",
        "url": url or None,
        "skills": skills,
    }
    record["source_key"] = build_source_key(record)
    return record


def deduplicate_vacancies(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    uniq: dict[str, dict[str, Any]] = {}
    for record in records:
        key = record["source_key"]
        if key not in uniq:
            uniq[key] = record
    return list(uniq.values())