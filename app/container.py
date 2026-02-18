from dependency_injector import containers, providers

from app.settings import Settings
from src.infrastructure.dbs.postgre import create_engine, create_session_factory
from src.infrastructure.dbs.redis import RedisConnection
from src.infrastructure.integrations.email_service import EmailService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.presentation.depends.session",
            "src.presentation.depends.security",
            "src.presentation.depends.controllers",
        ]
    )

    settings = Settings()

    engine = providers.Singleton(create_engine, db_url=settings.db_url, echo=False)

    session_factory = providers.Resource(
        create_session_factory, engine=engine
    )

    redis = providers.Resource(RedisConnection, url=settings.REDIS_URL)

    email_service = providers.Factory(
        EmailService,
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        from_email=settings.SMTP_FROM,
    )

    hash_service = providers.Factory(
        HashService,
    )

    jwt_service = providers.Factory(
        JWTService,
        secret_key=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    email_otp_service = providers.Factory(
        EmailOtpService,
        email_service=email_service,
        redis=redis,
        otp_ttl=settings.OTP_TTL,
    )
