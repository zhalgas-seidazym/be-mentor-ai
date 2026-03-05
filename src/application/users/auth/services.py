import random
import string
import secrets
import hashlib
import base64
from typing import Optional
from urllib.parse import urlencode

import bcrypt
import httpx
from fastapi import HTTPException, status as s
from redis.asyncio import Redis

from src.domain.interfaces import IEmailService


class EmailOtpService:
    def __init__(self, email_service: IEmailService, redis: Redis, otp_ttl: int = 300):
        self.email_service = email_service
        self.redis = redis
        self.otp_ttl = otp_ttl

    async def send_otp(self, email: str, ttl: Optional[int] = None) -> None:
        redis_key = f"otp:{email}"
        existed_key = await self.redis.get(redis_key)
        if existed_key:
            ttl = await self.redis.ttl(redis_key)
            raise HTTPException(
                status_code=s.HTTP_400_BAD_REQUEST,
                detail=f"OTP code already sent. Try again in {ttl} seconds."
            )
        otp = ''.join(random.choices(string.digits, k=6))
        await self.email_service.send_email(
            to_email=email,
            subject="Nomad Trip OTP Code",
            body=f"OTP code: {otp}",
        )

        await self.redis.set(redis_key, ex=self.otp_ttl or ttl, value=otp)
        print(await self.redis.get(redis_key))

    async def verify_otp(self, email: str, code: str) -> None:
        redis_key = f"otp:{email}"
        stored_otp = await self.redis.get(redis_key)

        if not stored_otp or stored_otp != code:
            raise HTTPException(status_code=s.HTTP_400_NOT_FOUND, detail="Incorrect or expired OTP")

        await self.redis.delete(redis_key)


class HashService:

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )


class OAuthService:
    def __init__(
            self,
            redis: Redis,
            google_client_id: str,
            google_client_secret: str,
            google_redirect_uri: str,
            state_ttl: int = 600,
    ):
        self.redis = redis
        self.google_client_id = google_client_id
        self.google_client_secret = google_client_secret
        self.google_redirect_uri = google_redirect_uri
        self.state_ttl = state_ttl

    @staticmethod
    def _pkce_pair() -> tuple[str, str]:
        verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
        return verifier, challenge

    async def build_authorization_url(self, provider: str) -> dict[str, str]:
        state = secrets.token_urlsafe(32)
        verifier, challenge = self._pkce_pair()

        if provider != "google":
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Unsupported OAuth provider")

        if not self.google_client_id or not self.google_redirect_uri:
            raise HTTPException(status_code=s.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth is not configured")

        params = {
            "client_id": self.google_client_id,
            "redirect_uri": self.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        await self.redis.set(f"oauth:state:{provider}:{state}", verifier, ex=self.state_ttl)
        return {
            "provider": provider,
            "authorization_url": auth_url,
            "state": state,
        }

    async def exchange_code_for_email(self, provider: str, code: str, state: str) -> dict[str, str]:
        redis_key = f"oauth:state:{provider}:{state}"
        verifier = await self.redis.get(redis_key)
        if not verifier:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="OAUTH_STATE_INVALID")

        await self.redis.delete(redis_key)

        if provider != "google":
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="Unsupported OAuth provider")

        email, email_verified = await self._google_email_from_code(
            code=code,
            verifier=verifier,
        )

        if not email_verified:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="OAUTH_EMAIL_NOT_VERIFIED")

        return {
            "email": email,
            "provider": provider,
        }

    async def _google_email_from_code(
        self,
        code: str,
        verifier: str,
    ) -> tuple[str, bool]:
        token_data = {
            "code": code,
            "client_id": self.google_client_id,
            "client_secret": self.google_client_secret,
            "redirect_uri": self.google_redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": verifier,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="OAUTH_CODE_INVALID")

            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="OAUTH_PROVIDER_ERROR")

            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_resp.status_code != 200:
                raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="OAUTH_PROVIDER_ERROR")

            payload = userinfo_resp.json()

        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=s.HTTP_400_BAD_REQUEST, detail="OAUTH_PROVIDER_ERROR")

        return email, bool(payload.get("email_verified"))
