from datetime import datetime

from airflow.sdk import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    dag_id="healthcheck_project",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["mentor-ai", "healthcheck"],
)
def healthcheck_project():
    @task
    def check_project_db():
        hook = PostgresHook(postgres_conn_id="mentorai_db")
        result = hook.get_first("SELECT 1;")
        print(f"DB response: {result}")
        return result[0]

    check_project_db()


healthcheck_project()