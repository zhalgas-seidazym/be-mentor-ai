from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError

class JWTService:
    def __init__(self, secret_key: str, algorithm: str, access_token_expire_minutes: int):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def encode_token(self, data: dict, expires_delta: Optional[int] = None, is_access_token: bool = True) -> str:
        to_encode = data.copy()
        if is_access_token:
            expire = datetime.utcnow() + timedelta(minutes=expires_delta or self.access_token_expire_minutes)
        else:
            expire = datetime.utcnow() + timedelta(minutes=expires_delta or self.access_token_expire_minutes * 24 * 7)
        to_encode.update({"exp": int(expire.timestamp())})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )