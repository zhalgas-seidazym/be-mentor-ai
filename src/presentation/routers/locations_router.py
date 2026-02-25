from typing import Annotated, Optional

from fastapi import APIRouter, status as s, Query, Depends

from src.application.locations.dtos import CountryDTO, CityDTO
from src.application.locations.interfaces import ILocationController
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.domain.responses import RESPONSE_404
from src.presentation.depends.controllers import get_location_controller


router = APIRouter(
    prefix="/locations",
    tags=["locations"]
)

@router.get(
    '/country',
    status_code=s.HTTP_200_OK,
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
    status_code=s.HTTP_200_OK,
    response_model=CountryDTO,
    responses={
        s.HTTP_404_NOT_FOUND: RESPONSE_404
    }
)
async def get_country_by_id(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        country_id: int,
):
    return await controller.get_country_by_id(country_id=country_id)

@router.get(
    '/city',
    status_code=s.HTTP_200_OK,
    response_model=PaginationDTO[CityDTO],
)
async def get_city_by_name_and_country_id(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        q: Optional[str] = Query(None),
        country_id: Optional[int] = Query(None),
        populate_country: bool = Query(False),
        pagination: PaginationSchema = Depends(PaginationSchema.as_query()),
):
    return await controller.get_city_by_name_and_country_id(
        pagination=PaginationDTO[CityDTO](**pagination.dict()),
        q=q,
        country_id=country_id,
        populate_country=populate_country,
    )

@router.get(
    '/city/{city_id}',
    status_code=s.HTTP_200_OK,
    response_model=CityDTO,
    responses={
        s.HTTP_404_NOT_FOUND: RESPONSE_404
    }
)
async def get_city_by_id(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        city_id: int,
        populate_country: bool = Query(False),
):
    return await controller.get_city_by_id(city_id=city_id, populate_country=populate_country)