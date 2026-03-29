from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from airflow.providers.postgres.hooks.postgres import PostgresHook

from lib.fx_sources import FxRateRow


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def upsert_exchange_rates(
    postgres_conn_id: str,
    rates: list[FxRateRow],
) -> dict[str, Any]:
    if not rates:
        return {"rows_upserted": 0, "rate_date": None}

    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            for row in rates:
                cur.execute(
                    """
                    INSERT INTO public.exchange_rates (
                        rate_date,
                        currency_code,
                        nominal,
                        rate_value_kzt,
                        rate_per_unit_kzt,
                        source,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (rate_date, currency_code, source)
                    DO UPDATE SET
                        nominal = EXCLUDED.nominal,
                        rate_value_kzt = EXCLUDED.rate_value_kzt,
                        rate_per_unit_kzt = EXCLUDED.rate_per_unit_kzt,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        row.rate_date,
                        row.currency_code,
                        row.nominal,
                        row.rate_value_kzt,
                        row.rate_per_unit_kzt,
                        row.source,
                        now_utc(),
                        now_utc(),
                    ),
                )

        conn.commit()

        return {
            "rows_upserted": len(rates),
            "rate_date": rates[0].rate_date.isoformat(),
            "currencies": [r.currency_code for r in rates],
            "source": rates[0].source,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_latest_rates_to_kzt(
    postgres_conn_id: str,
    as_of_date: date | None = None,
) -> dict[str, float]:
    """
    Возвращает latest available rate_per_unit_kzt для каждой валюты
    на дату <= as_of_date.
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    if as_of_date is None:
        as_of_date = date.today()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (currency_code)
                    currency_code,
                    rate_per_unit_kzt,
                    rate_date
                FROM public.exchange_rates
                WHERE rate_date <= %s
                ORDER BY currency_code, rate_date DESC
                """,
                (as_of_date,),
            )
            rows = cur.fetchall()

        result = {row[0]: float(row[1]) for row in rows}
        if "KZT" not in result:
            result["KZT"] = 1.0

        return result
    finally:
        conn.close()