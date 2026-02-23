from datetime import time, datetime
from typing import Optional

from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import Container
from src.application.users.interfaces import IUserRepository
from src.domain.interfaces import IJWTService
from src.domain.value_objects import TokenType
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

    if payload.get("type") != TokenType.ACCESS.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    exp = payload.get('exp')
    if datetime.utcnow() >= datetime.utcfromtimestamp(exp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user = await user_repo.get_by_id(payload['user_id'])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    return user


@inject
async def get_refresh_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    jwt_service: IJWTService = Depends(Provide[Container.jwt_service]),
    user_repo: IUserRepository = Depends(get_user_repository),
):
    if token is None or not token.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    payload = jwt_service.decode_token(token.credentials)

    if payload.get("type") != TokenType.REFRESH.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    exp = payload.get("exp")
    if not exp or datetime.utcnow() >= datetime.utcfromtimestamp(exp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = await user_repo.get_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return user


@inject
async def get_reset_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    jwt_service: IJWTService = Depends(Provide[Container.jwt_service]),
    user_repo: IUserRepository = Depends(get_user_repository),
):
    if token is None or not token.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if token.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    payload = jwt_service.decode_token(token.credentials)

    if payload.get("type") != TokenType.PASSWORD_RESET.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token")

    exp = payload.get("exp")
    if not exp or datetime.utcnow() >= datetime.utcfromtimestamp(exp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Reset token expired")

    user = await user_repo.get_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token")

    return user