from fastapi import FastAPI

from .container import Container


container = Container()
app = FastAPI()
app.container = container
