from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.dbs.postgre import Base
from src.domain.base_model import TimestampMixin


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )