from fastapi import FastAPI

from .container import Container
from src.presentation.routers.user_router import router as ur


container = Container()
app = FastAPI()
app.container = container

app.include_router(ur)