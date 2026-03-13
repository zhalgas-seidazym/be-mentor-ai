from typing import Annotated, Optional

from fastapi import APIRouter, status as s, Query, Depends

from src.application.locations.dtos import CountryDTO, CityDTO
from src.application.locations.interfaces import ILocationController
from src.application.users.dtos import UserDTO
from src.domain.base_dto import PaginationDTO
from src.domain.base_schema import PaginationSchema
from src.domain.responses import RESPONSE_404, RESPONSE_401
from src.presentation.depends.controllers import get_location_controller
from src.presentation.depends.security import get_access_user

router = APIRouter(
    prefix="/locations",
    tags=["locations"]
)

@router.get(
    '/country',
    summary="Search countries",
    status_code=s.HTTP_200_OK,
    response_model=PaginationDTO[CountryDTO],
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401
    }
)
async def get_countries_by_name(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        pagination: PaginationSchema = Depends(PaginationSchema.as_query()),
        q: Optional[str] = Query(None),
        user: UserDTO = Depends(get_access_user)
):
    return await controller.get_countries_by_name(
        pagination=PaginationDTO[CountryDTO](**pagination.dict()), q=q
    )

@router.get(
    '/country/{country_id}',
    summary="Get country by id",
    status_code=s.HTTP_200_OK,
    response_model=CountryDTO,
    responses={
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401
    }
)
async def get_country_by_id(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        country_id: int,
        user: UserDTO = Depends(get_access_user)
):
    return await controller.get_country_by_id(country_id=country_id)

@router.get(
    '/city',
    summary="Search cities",
    status_code=s.HTTP_200_OK,
    response_model=PaginationDTO[CityDTO],
    responses={
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401
    }
)
async def get_city_by_name_and_country_id(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        q: Optional[str] = Query(None),
        country_id: Optional[int] = Query(None),
        populate_country: bool = Query(False),
        pagination: PaginationSchema = Depends(PaginationSchema.as_query()),
        user: UserDTO = Depends(get_access_user)
):
    return await controller.get_city_by_name_and_country_id(
        pagination=PaginationDTO[CityDTO](**pagination.dict()),
        q=q,
        country_id=country_id,
        populate_country=populate_country,
    )

@router.get(
    '/city/{city_id}',
    summary="Get city by id",
    status_code=s.HTTP_200_OK,
    response_model=CityDTO,
    responses={
        s.HTTP_404_NOT_FOUND: RESPONSE_404,
        s.HTTP_401_UNAUTHORIZED: RESPONSE_401
    }
)
async def get_city_by_id(
        controller: Annotated[ILocationController, Depends(get_location_controller)],
        city_id: int,
        populate_country: bool = Query(False),
        user: UserDTO = Depends(get_access_user)
):
    return await controller.get_city_by_id(city_id=city_id, populate_country=populate_country)
