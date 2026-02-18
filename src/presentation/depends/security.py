from datetime import time, datetime
from typing import Optional

from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import Container
from src.application.users.interfaces import IUserRepository
from src.domain.interfaces import IJWTService
from src.presentation.depends.repositories import get_user_repository

http_bearer = HTTPBearer()

@inject
async def get_current_user(
        token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
        jwt_service: IJWTService = Depends(Provide[Container.jwt_service]),
        user_repo: IUserRepository = Depends(get_user_repository),
):
    if token is None or not token.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if token.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    payload = jwt_service.decode_token(token.credentials)
    exp = payload['exp']
    if datetime.utcnow() >= datetime.utcfromtimestamp(exp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user = await user_repo.get_by_id(payload['user_id'])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    return user
