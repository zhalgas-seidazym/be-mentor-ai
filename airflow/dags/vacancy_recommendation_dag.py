from __future__ import annotations

import os
from typing import Any

import pendulum

from airflow.sdk import dag, get_current_context, task

from lib.recommendation_repository import (
    build_recommendations_for_user,
    fetch_recommendation_users,
    replace_user_vacancies,
)


DAG_ID = "vacancy_recommendation_dag"
POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "mentorai_db")
TOP_K = int(os.getenv("VACANCY_RECOMMENDATION_TOP_K", "10"))


@dag(
    dag_id=DAG_ID,
    schedule="45 3 * * *",
    start_date=pendulum.datetime(2026, 3, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["mentorai", "vacancies", "recommendation"],
)
def vacancy_recommendation_dag():
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
    def resolve_users(conf: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Логика user_id такая же, как в ingestion / analytics:
        - если user_id передан -> только этот пользователь
        - если user_id не передан -> все пользователи с direction_id и city_id
        """
        return fetch_recommendation_users(
            postgres_conn_id=POSTGRES_CONN_ID,
            user_id=conf["user_id"],
        )

    @task
    def recommend_and_save(conf: dict[str, Any], users: list[dict[str, Any]]) -> dict[str, Any]:
        if not users:
            return {
                "user_id": conf["user_id"],
                "users_total": 0,
                "users_with_recommendations": 0,
                "candidate_vacancies_total": 0,
                "recommended_rows_total": 0,
                "inserted_rows": 0,
            }

        all_rows: list[dict[str, Any]] = []
        users_with_recommendations = 0
        candidate_vacancies_total = 0

        for user_row in users:
            result = build_recommendations_for_user(
                postgres_conn_id=POSTGRES_CONN_ID,
                user_row=user_row,
                top_k=TOP_K,
            )
            candidate_vacancies_total += result["candidate_vacancies"]

            if result["recommended_vacancies"] > 0:
                users_with_recommendations += 1

            all_rows.extend(result["rows"])

        save_stats = replace_user_vacancies(
            postgres_conn_id=POSTGRES_CONN_ID,
            affected_user_ids=[int(u["user_id"]) for u in users],
            recommendation_rows=all_rows,
        )

        return {
            "user_id": conf["user_id"],
            "users_total": len(users),
            "users_with_recommendations": users_with_recommendations,
            "candidate_vacancies_total": candidate_vacancies_total,
            "recommended_rows_total": len(all_rows),
            "inserted_rows": save_stats["inserted_rows"],
        }

    conf = read_conf()
    users = resolve_users(conf)
    summary = recommend_and_save(conf, users)

    conf >> users >> summary


vacancy_recommendation_dag()