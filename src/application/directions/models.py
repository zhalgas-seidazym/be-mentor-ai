from sqlalchemy import Integer, String, Text, UniqueConstraint, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.dbs.postgre import Base
from src.domain.base_model import TimestampMixin


class Direction(Base, TimestampMixin):
    __tablename__ = "directions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # relations
    salaries: Mapped[list["Salary"]] = relationship(
        "Salary",
        back_populates="direction",
        cascade="all, delete-orphan",
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="direction",
    )


class Salary(Base, TimestampMixin):
    __tablename__ = "salaries"

    __table_args__ = (
        UniqueConstraint(
            "direction_id",
            "city_id",
            name="uq_direction_city_salary"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    direction_id: Mapped[int] = mapped_column(
        ForeignKey("directions.id", ondelete="CASCADE"),
        nullable=False,
    )

    city_id: Mapped[int] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    # relations
    direction: Mapped["Direction"] = relationship(
        "Direction",
        back_populates="salaries",
    )

    city: Mapped["City"] = relationship(
        "City",
    )