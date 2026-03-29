from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

import httpx
from bs4 import BeautifulSoup


NBRK_DAILY_URL = "https://nationalbank.kz/en/exchangerates/ezhednevnye-oficialnye-rynochnye-kursy-valyut"
SOURCE_NAME = "NBRK_DAILY_HTML"
SUPPORTED_CURRENCIES = {"KZT", "USD", "EUR", "RUB"}


@dataclass
class FxRateRow:
    rate_date: date
    currency_code: str
    nominal: int
    rate_value_kzt: float
    rate_per_unit_kzt: float
    source: str = SOURCE_NAME


def _parse_rate_date(page_text: str) -> date:
    match = re.search(
        r"Official\s*\(market\)\s*Exchange\s*Rates\s*on:\s*(\d{4}-\d{2}-\d{2})",
        page_text,
        flags=re.IGNORECASE,
    )
    if not match:
        raise RuntimeError("Could not parse rate date from NBRK page")
    return date.fromisoformat(match.group(1))


def _parse_float(value: str) -> float:
    return float(value.replace(",", ".").replace(" ", "").strip())


def fetch_nbrk_rates_to_kzt() -> list[FxRateRow]:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
        "Accept-Language": "en",
    }

    with httpx.Client(timeout=30.0, follow_redirects=True, headers=headers) as client:
        response = client.get(NBRK_DAILY_URL)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    raw_text = soup.get_text("\n", strip=True)
    rate_date = _parse_rate_date(raw_text)

    # Ключевой фикс:
    # схлопываем ВСЕ переводы строк/табуляции/множественные пробелы в один пробел
    normalized_text = re.sub(r"\s+", " ", raw_text).strip()

    rows: list[FxRateRow] = []

    # Ищем по всему нормализованному тексту последовательности вида:
    # 1 US DOLLAR USD / KZT 482.53
    # 10 ARMENIAN DRAM AMD / KZT 12.89
    # 1000 IRANIAN RIAL IRR / KZT 0.4
    pattern = re.compile(
        r"(?P<nominal>\d+)\s+"
        r"(?P<name>[A-Z][A-Z\s\-']+?)\s+"
        r"(?P<code>[A-Z]{3})\s*/\s*KZT\s+"
        r"(?P<rate>\d+(?:[.,]\d+)?)"
    )

    for match in pattern.finditer(normalized_text):
        currency_code = match.group("code").upper().strip()
        if currency_code not in SUPPORTED_CURRENCIES:
            continue

        nominal = int(match.group("nominal"))
        rate_value_kzt = _parse_float(match.group("rate"))
        rate_per_unit_kzt = round(rate_value_kzt / nominal, 8)

        rows.append(
            FxRateRow(
                rate_date=rate_date,
                currency_code=currency_code,
                nominal=nominal,
                rate_value_kzt=rate_value_kzt,
                rate_per_unit_kzt=rate_per_unit_kzt,
            )
        )

    # гарантируем наличие KZT
    if not any(r.currency_code == "KZT" for r in rows):
        rows.append(
            FxRateRow(
                rate_date=rate_date,
                currency_code="KZT",
                nominal=1,
                rate_value_kzt=1.0,
                rate_per_unit_kzt=1.0,
            )
        )

    # убираем дубли по коду валюты
    unique_by_code: dict[str, FxRateRow] = {}
    for row in rows:
        unique_by_code[row.currency_code] = row

    result = sorted(unique_by_code.values(), key=lambda x: x.currency_code)

    found_codes = {r.currency_code for r in result}
    required = {"KZT", "USD", "EUR", "RUB"}
    missing = required - found_codes

    if missing:
        preview_matches = [
            {
                "nominal": m.group("nominal"),
                "name": m.group("name"),
                "code": m.group("code"),
                "rate": m.group("rate"),
            }
            for m in list(pattern.finditer(normalized_text))[:20]
        ]

        raise RuntimeError(
            f"NBRK FX page parsed, but missing currencies: {sorted(missing)}; "
            f"parsed_codes={sorted(found_codes)}; preview_matches={preview_matches}"
        )

    return result