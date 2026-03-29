from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from airflow.providers.postgres.hooks.postgres import PostgresHook

from lib.fx_repository import load_latest_rates_to_kzt


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def convert_to_kzt(amount: float | None, currency: str | None, fx_rates_to_kzt: dict[str, float]) -> float | None:
    if amount is None or currency is None:
        return None

    cur = str(currency).upper().strip()
    rate = fx_rates_to_kzt.get(cur)
    if rate is None:
        return None

    return round(float(amount) * float(rate), 2)


def load_vacancies_for_target(
    postgres_conn_id: str,
    direction_id: int,
    city_id: int,
) -> list[dict[str, Any]]:
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    salary_amount,
                    salary_currency
                FROM public.vacancies
                WHERE direction_id = %s
                  AND city_id = %s
                """,
                (direction_id, city_id),
            )
            rows = cur.fetchall()

        return [
            {
                "vacancy_id": int(row[0]),
                "salary_amount": row[1],
                "salary_currency": row[2],
            }
            for row in rows
        ]
    finally:
        conn.close()


def compute_average_salary_kzt_for_target(
    postgres_conn_id: str,
    direction_id: int,
    city_id: int,
    as_of_date: date | None = None,
) -> dict[str, Any] | None:
    fx_rates_to_kzt = load_latest_rates_to_kzt(
        postgres_conn_id=postgres_conn_id,
        as_of_date=as_of_date,
    )

    vacancies = load_vacancies_for_target(
        postgres_conn_id=postgres_conn_id,
        direction_id=direction_id,
        city_id=city_id,
    )

    salary_values_kzt: list[float] = []
    skipped_missing_fx = 0

    for vacancy in vacancies:
        salary_kzt = convert_to_kzt(
            amount=vacancy["salary_amount"],
            currency=vacancy["salary_currency"],
            fx_rates_to_kzt=fx_rates_to_kzt,
        )
        if salary_kzt is None:
            if vacancy["salary_amount"] is not None and vacancy["salary_currency"] is not None:
                skipped_missing_fx += 1
            continue

        salary_values_kzt.append(salary_kzt)

    if not salary_values_kzt:
        return None

    avg_salary_kzt = round(sum(salary_values_kzt) / len(salary_values_kzt), 2)

    return {
        "direction_id": direction_id,
        "city_id": city_id,
        "amount": avg_salary_kzt,
        "currency": "KZT",
        "vacancies_with_salary": len(salary_values_kzt),
        "skipped_missing_fx": skipped_missing_fx,
    }


def refresh_salary_row_for_target(
    postgres_conn_id: str,
    direction_id: int,
    city_id: int,
    amount: float | None,
    currency: str | None,
) -> None:
    """
    Обновляем агрегат в salaries delete+insert,
    чтобы не зависеть от наличия уникального индекса на (direction_id, city_id).
    """
    hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    conn = hook.get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM public.salaries
                WHERE direction_id = %s
                  AND city_id = %s
                """,
                (direction_id, city_id),
            )

            if amount is not None and currency is not None:
                cur.execute(
                    """
                    INSERT INTO public.salaries (
                        direction_id,
                        city_id,
                        amount,
                        currency,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (direction_id,
                        city_id,
                        amount,
                        currency,
                        now_utc(),
                        now_utc(),
                    ),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def recompute_salary_analytics_for_target(
    postgres_conn_id: str,
    target: dict[str, Any],
) -> dict[str, Any]:
    direction_id = int(target["direction_id"])
    city_id = int(target["city_id"])

    stats = compute_average_salary_kzt_for_target(
        postgres_conn_id=postgres_conn_id,
        direction_id=direction_id,
        city_id=city_id,
    )

    if stats is None:
        refresh_salary_row_for_target(
            postgres_conn_id=postgres_conn_id,
            direction_id=direction_id,
            city_id=city_id,
            amount=None,
            currency=None,
        )
        return {
            "direction_id": direction_id,
            "city_id": city_id,
            "direction_name": target["direction_name"],
            "city_name": target["city_name"],
            "updated": False,
            "amount": None,
            "currency": None,
            "vacancies_with_salary": 0,
            "skipped_missing_fx": 0,
        }

    refresh_salary_row_for_target(
        postgres_conn_id=postgres_conn_id,
        direction_id=direction_id,
        city_id=city_id,
        amount=stats["amount"],
        currency=stats["currency"],
    )

    return {
        "direction_id": direction_id,
        "city_id": city_id,
        "direction_name": target["direction_name"],
        "city_name": target["city_name"],
        "updated": True,
        "amount": stats["amount"],
        "currency": stats["currency"],
        "vacancies_with_salary": stats["vacancies_with_salary"],
        "skipped_missing_fx": stats["skipped_missing_fx"],
    }