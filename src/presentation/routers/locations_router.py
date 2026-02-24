from typing import Annotated, Optional

from fastapi import APIRouter, status, HTTPException, Query, Depends

from src.application.locations.dtos import CountryDTO
from src.application.locations.interfaces import ILocationController
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.presentation.depends.controllers import get_location_controller


router = APIRouter(
    prefix="/locations",
    tags=["locations"]
)

@router.get(
    '/country',
    response_model=PaginationDTO[CountryDTO],
    status_code=status.HTTP_200_OK,
)
async def get_countries_pagination(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        pagination: PaginationSchema = Depends(PaginationSchema.as_query()),
        q: Optional[str] = Query(None),
):
    return await controller.get_countries_by_name(
        pagination=PaginationDTO[CountryDTO](**pagination.dict()), q=q
    )