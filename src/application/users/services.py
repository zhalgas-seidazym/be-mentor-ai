import random
import string

from fastapi import HTTPException, status as s
from redis.asyncio import Redis

from src.domain.interfaces import IEmailService


class EmailOtpService:
    def __init__(self, email_service: IEmailService, redis: Redis, otp_ttl: int = 300):
        self.email_service = email_service
        self.redis = redis
        self.otp_ttl = otp_ttl

    async def send_otp(self, email: str) -> None:
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

        await self.redis.set(redis_key, ex=self.otp_ttl, value=otp)
        print(await self.redis.get(redis_key))

    async def verify_otp(self, email: str, code: str) -> None:
        redis_key = f"otp:{email}"
        stored_otp = await self.redis.get(redis_key)

        if not stored_otp or stored_otp != code:
            raise HTTPException(status_code=s.HTTP_404_NOT_FOUND, detail="Incorrect or expired OTP")

        await self.redis.delete(redis_key)
