from typing import Optional

from sqlalchemy import Integer, String, Boolean, ForeignKey, UniqueConstraint
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

    # --- Career ---

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


class UserSkill(Base):
    __tablename__ = "user_skills"

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )

    to_learn: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # --- Relations ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_skills",
    )

    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="user_skills",
    )