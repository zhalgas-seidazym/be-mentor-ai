from typing import Optional

from sqlalchemy import Integer, String, ForeignKey, Numeric, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.dbs.postgre import Base
from src.domain.base_model import TimestampMixin
from src.domain.value_objects import VacancyType


class Vacancy(Base, TimestampMixin):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    direction_id: Mapped[int] = mapped_column(
        ForeignKey("directions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    salary_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    salary_currency: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    vacancy_type: Mapped[VacancyType] = mapped_column(
        SQLEnum(VacancyType, name="vacancy_type"),
        nullable=False,
    )

    url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
    )

    # --- Relations ---
    direction: Mapped["Direction"] = relationship(
        "Direction",
    )

    city: Mapped["City"] = relationship(
        "City",
    )

    vacancy_skills: Mapped[list["VacancySkill"]] = relationship(
        "VacancySkill",
        back_populates="vacancy",
        cascade="all, delete-orphan",
    )

    user_vacancies: Mapped[list["UserVacancy"]] = relationship(
        "UserVacancy",
        back_populates="vacancy",
        cascade="all, delete-orphan",
    )


class VacancySkill(Base):
    __tablename__ = "vacancy_skills"

    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE"),
        primary_key=True,
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # --- Relations ---
    vacancy: Mapped["Vacancy"] = relationship(
        "Vacancy",
        back_populates="vacancy_skills",
    )

    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="vacancy_skills",
    )


class UserVacancy(Base):
    __tablename__ = "user_vacancies"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # --- Relations ---
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_vacancies",
    )

    vacancy: Mapped["Vacancy"] = relationship(
        "Vacancy",
        back_populates="user_vacancies",
    )
