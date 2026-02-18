from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.base_model import TimestampMixin
from src.infrastructure.dbs.postgre import Base


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # --- Auth ---
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )
    password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # --- Profile ---
    name: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # --- Onboarding ---
    is_onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # --- Career ---

    # --- Region ---

    # --- Relations ---
