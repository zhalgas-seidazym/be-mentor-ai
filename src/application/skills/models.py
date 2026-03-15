from typing import Optional

from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    user_skills: Mapped[list["UserSkill"]] = relationship(
        "UserSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    learning_recommendations: Mapped[list["LearningRecommendation"]] = relationship(
        "LearningRecommendation",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    vacancy_skills: Mapped[list["VacancySkill"]] = relationship(
        "VacancySkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )


class UserSkill(Base):
    __tablename__ = "user_skills"

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

    match_percentage: Mapped[Optional[float]] = mapped_column(
        nullable=True,
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
