from typing import Annotated

from dependency_injector.wiring import inject, Provide
from fastapi import FastAPI, Depends

from src.application.skills.interfaces import ISkillSearchService
from .container import Container
from src.presentation.routers import (
    users_router as ur,
    skills_router as sr,
    locations_router as lr,
    directions_router as dr,
)


container = Container()
app = FastAPI(
    prefix="/api",
)
app.container = container

@app.on_event("startup")
async def startup():
    skill_search: ISkillSearchService = Container.skill_search_service()
    # await skill_search.delete_index()
    check = await skill_search.create_index_if_not_exists()
    print(check)

app.include_router(ur.router)
app.include_router(sr.router)
app.include_router(lr.router)
app.include_router(dr.router)