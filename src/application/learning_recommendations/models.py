from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.dbs.postgre import Base
from src.domain.base_model import TimestampMixin


class LearningRecommendation(Base, TimestampMixin):
    __tablename__ = "learning_recommendations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="learning_recommendations",
    )
