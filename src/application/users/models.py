from typing import Optional

from datetime import date

from sqlalchemy import Integer, String, Boolean, ForeignKey, Date
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
    name: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    # --- Onboarding ---
    is_onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # --- Streak ---
    current_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    longest_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_interview_day: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="UTC",
    )

    # --- Career ---

    direction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("directions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Region ---

    city_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Relations ---
    city: Mapped[Optional["City"]] = relationship(
        "City",
        back_populates="users",
        lazy="selectin",
    )

    user_skills: Mapped[list["UserSkill"]] = relationship(
        "UserSkill",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    user_questions: Mapped[list["UserQuestion"]] = relationship(
        "UserQuestion",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    interview_sessions: Mapped[list["InterviewSession"]] = relationship(
        "InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    direction: Mapped[Optional["Direction"]] = relationship(
        "Direction",
        back_populates="users",
    )


