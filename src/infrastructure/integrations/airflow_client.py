import httpx
import uuid


class AirflowClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password

    async def _get_token(self) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/auth/token",
                json={
                    "username": self.username,
                    "password": self.password,
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def trigger_dag(self, dag_id: str, conf: dict) -> dict:
        token = await self._get_token()

        payload = {
            "dag_run_id": f"manual__vacancy_ingestion_dag__{conf["user_id"]}__{uuid.uuid4().hex}",
            "logical_date": None,
            "conf": conf,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v2/dags/{dag_id}/dagRuns",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            if response.is_error:
                raise RuntimeError(
                    f"Airflow trigger failed: status={response.status_code}, body={response.text}"
                )

            return response.json()