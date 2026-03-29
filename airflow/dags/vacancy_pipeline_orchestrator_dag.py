from __future__ import annotations

from typing import Any

import pendulum

from airflow.sdk import dag, get_current_context, task
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator


DAG_ID = "vacancy_pipeline_orchestrator_dag"


@dag(
    dag_id=DAG_ID,
    schedule=None,
    start_date=pendulum.datetime(2026, 3, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["mentorai", "vacancies", "orchestrator"],
)
def vacancy_pipeline_orchestrator_dag():
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
    def summarize(conf: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "success",
            "user_id": conf["user_id"],
            "pipeline": [
                "vacancy_ingestion_dag",
                "vacancy_salary_analytics_dag",
                "vacancy_recommendation_dag",
            ],
        }

    conf = read_conf()

    trigger_ingestion = TriggerDagRunOperator(
        task_id="trigger_ingestion",
        trigger_dag_id="vacancy_ingestion_dag",
        conf=conf,
        wait_for_completion=True,
        poke_interval=20,
        allowed_states=["success"],
        failed_states=["failed"],
    )

    trigger_salary_analytics = TriggerDagRunOperator(
        task_id="trigger_salary_analytics",
        trigger_dag_id="vacancy_salary_analytics_dag",
        conf=conf,
        wait_for_completion=True,
        poke_interval=20,
        allowed_states=["success"],
        failed_states=["failed"],
    )

    trigger_recommendation = TriggerDagRunOperator(
        task_id="trigger_recommendation",
        trigger_dag_id="vacancy_recommendation_dag",
        conf=conf,
        wait_for_completion=True,
        poke_interval=20,
        allowed_states=["success"],
        failed_states=["failed"],
    )

    done = summarize(conf)

    conf >> trigger_ingestion >> trigger_salary_analytics >> trigger_recommendation >> done


vacancy_pipeline_orchestrator_dag()