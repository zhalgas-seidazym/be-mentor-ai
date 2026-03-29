from __future__ import annotations

import os
from typing import Any

import pendulum

from airflow.sdk import dag, task

from lib.fx_repository import upsert_exchange_rates
from lib.fx_sources import fetch_nbrk_rates_to_kzt


DAG_ID = "fx_rates_sync_dag"
POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "mentorai_db")


@dag(
    dag_id=DAG_ID,
    schedule="50 2 * * *",
    start_date=pendulum.datetime(2026, 3, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["mentorai", "fx", "rates"],
)
def fx_rates_sync_dag():
    @task
    def fetch_rates() -> list[dict[str, Any]]:
        rows = fetch_nbrk_rates_to_kzt()
        return [
            {
                "rate_date": r.rate_date.isoformat(),
                "currency_code": r.currency_code,
                "nominal": r.nominal,
                "rate_value_kzt": r.rate_value_kzt,
                "rate_per_unit_kzt": r.rate_per_unit_kzt,
                "source": r.source,
            }
            for r in rows
        ]

    @task
    def store_rates(rows: list[dict[str, Any]]) -> dict[str, Any]:
        from lib.fx_sources.nbrk_html import FxRateRow
        import datetime as dt

        typed_rows = [
            FxRateRow(
                rate_date=dt.date.fromisoformat(r["rate_date"]),
                currency_code=r["currency_code"],
                nominal=int(r["nominal"]),
                rate_value_kzt=float(r["rate_value_kzt"]),
                rate_per_unit_kzt=float(r["rate_per_unit_kzt"]),
                source=r["source"],
            )
            for r in rows
        ]
        return upsert_exchange_rates(
            postgres_conn_id=POSTGRES_CONN_ID,
            rates=typed_rows,
        )

    rows = fetch_rates()
    store_rates(rows)


fx_rates_sync_dag()