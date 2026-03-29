from __future__ import annotations

import os
from typing import Any

import pendulum

from airflow.sdk import dag, get_current_context, task

from lib.scope import fetch_target_scopes
from lib.salary_analytics_repository import recompute_salary_analytics_for_target


DAG_ID = "vacancy_salary_analytics_dag"
POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "mentorai_db")


@dag(
    dag_id=DAG_ID,
    schedule="30 3 * * *",
    start_date=pendulum.datetime(2026, 3, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["mentorai", "vacancies", "analytics", "salary"],
)
def vacancy_salary_analytics_dag():
    @task
    def read_conf() -> dict[str, Any]:
        context = get_current_context()
        dag_run = context.get("dag_run")
        conf = dag_run.conf if dag_run else {}

        user_id = conf.get("user_id")
        if user_id is not None:
            user_id = int(user_id)

        return {"user_id": user_id}

    @task
    def resolve_targets(conf: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Полностью повторяем target-логику ingestion DAG:
        - manual run с user_id -> target только пользователя
        - без user_id -> все уникальные пары из users
        """
        return fetch_target_scopes(
            postgres_conn_id=POSTGRES_CONN_ID,
            user_id=conf["user_id"],
        )

    @task
    def analyze_targets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for target in targets:
            result = recompute_salary_analytics_for_target(
                postgres_conn_id=POSTGRES_CONN_ID,
                target=target,
            )
            results.append(result)

        return results

    @task
    def summarize(conf: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
        updated_rows = sum(1 for r in results if r["updated"])
        skipped_rows = len(results) - updated_rows

        return {
            "base_currency": "KZT",
            "user_id": conf["user_id"],
            "targets_total": len(results),
            "targets_updated": updated_rows,
            "targets_without_salary": skipped_rows,
            "total_vacancies_with_salary": sum(r["vacancies_with_salary"] for r in results),
            "total_skipped_missing_fx": sum(r["skipped_missing_fx"] for r in results),
            "updated_targets": [
                {
                    "direction_id": r["direction_id"],
                    "city_id": r["city_id"],
                    "amount": r["amount"],
                    "currency": r["currency"],
                    "vacancies_with_salary": r["vacancies_with_salary"],
                }
                for r in results
                if r["updated"]
            ],
        }

    conf = read_conf()
    targets = resolve_targets(conf)
    analyzed = analyze_targets(targets)
    summary = summarize(conf, analyzed)

    conf >> targets >> analyzed >> summary


vacancy_salary_analytics_dag()