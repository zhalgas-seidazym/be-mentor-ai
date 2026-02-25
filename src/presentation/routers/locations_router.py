from typing import Annotated, Optional

from fastapi import APIRouter, status, HTTPException, Query, Depends

from src.application.locations.dtos import CountryDTO, CityDTO
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
    status_code=status.HTTP_200_OK,
    response_model=PaginationDTO[CountryDTO],
)
async def get_countries_by_name(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        pagination: PaginationSchema = Depends(PaginationSchema.as_query()),
        q: Optional[str] = Query(None),
):
    return await controller.get_countries_by_name(
        pagination=PaginationDTO[CountryDTO](**pagination.dict()), q=q
    )

@router.get(
    '/country/{country_id}',
    status_code=status.HTTP_200_OK,
    response_model=CountryDTO,
)
async def get_country_by_id(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        country_id: int,
):
    return await controller.get_country_by_id(country_id=country_id)

@router.get(
    '/city',
    status_code=status.HTTP_200_OK,
    response_model=PaginationDTO[CityDTO],
)
async def get_city_by_name_and_country_id(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
): ...