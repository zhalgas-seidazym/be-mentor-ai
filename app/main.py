from typing import Annotated

from dependency_injector.wiring import inject, Provide
from fastapi import FastAPI, Depends

from src.application.skills.interfaces import ISkillSearchService
from src.application.directions.interfaces import IDirectionSearchService
from .container import Container
from src.presentation.routers import (
    users_router as ur,
    auth_router as ar,
    skills_router as sr,
    locations_router as lr,
    directions_router as dr,
    modules_router as mr,
    questions_router as qr,
    interview_router as ir,
    learning_recommendations_router as lrr,
    vacancies_router as vr,
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
    await skill_search.create_index_if_not_exists()

    direction_search: IDirectionSearchService = Container.direction_search_service()
    # await direction_search.delete_index()
    await direction_search.create_index_if_not_exists()

app.include_router(ur.router)
app.include_router(ar.router)
app.include_router(sr.router)
app.include_router(lr.router)
app.include_router(dr.router)
app.include_router(mr.router)
app.include_router(qr.router)
app.include_router(ir.router)
app.include_router(lrr.router)
app.include_router(vr.router)
