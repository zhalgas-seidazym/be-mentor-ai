from datetime import datetime

from airflow.sdk import dag, task, get_current_context


@dag(
    dag_id="rebuild_user_profile",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["mentor-ai", "manual-trigger"],
)
def rebuild_user_profile():
    @task
    def read_conf():
        context = get_current_context()
        conf = context["dag_run"].conf or {}

        user_id = conf.get("user_id")
        direction_id = conf.get("direction_id")

        if not user_id:
            raise ValueError("user_id is required in dag_run.conf")

        print(
            {
                "user_id": user_id,
                "direction_id": direction_id,
            }
        )
        return conf

    read_conf()


rebuild_user_profile()