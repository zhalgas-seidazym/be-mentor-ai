from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.dbs.postgre import Base
from src.domain.base_model import TimestampMixin


class Country(Base, TimestampMixin):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    cities: Mapped[list["City"]] = relationship(
        back_populates="country",
        cascade="all, delete-orphan"
    )


class City(Base, TimestampMixin):
    __tablename__ = "cities"

    __table_args__ = (
        UniqueConstraint("name", "country_id", name="uq_city_country"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=False
    )

    country: Mapped["Country"] = relationship(
        back_populates="cities"
    )