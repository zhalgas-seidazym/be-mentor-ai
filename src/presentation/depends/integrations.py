from typing import Annotated

from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from app.container import Container
from src.infrastructure.integrations.airflow_client import AirflowClient


@inject
def get_airflow_client(
    airflow_client: Annotated[
        AirflowClient,
        Depends(Provide[Container.airflow_client]),
    ],
) -> AirflowClient:
    return airflow_client