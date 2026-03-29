from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status as s

from src.infrastructure.integrations.airflow_client import AirflowClient
from src.presentation.depends.integrations import get_airflow_client

router = APIRouter(
    prefix="/internal/airflow",
    tags=["airflow"],
)


@router.post(
    "/vacancy_pipeline_orchestrator_dag/{user_id}",
    status_code=s.HTTP_200_OK,
)
async def trigger_vacancy_pipeline_orchestrator_dag(
    user_id: int,
    airflow_client: Annotated[AirflowClient, Depends(get_airflow_client)],
) -> Any:
    try:
        return await airflow_client.trigger_dag(
            dag_id="vacancy_pipeline_orchestrator_dag",
            conf={
                "user_id": user_id
            },
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))