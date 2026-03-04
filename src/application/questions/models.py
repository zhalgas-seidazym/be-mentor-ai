from typing import Optional

from sqlalchemy import Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.dbs.postgre import Base
from src.domain.base_model import TimestampMixin
from src.domain.value_objects import QuestionStatus


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    ideal_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )

    # --- Relations ---
    skill: Mapped[Optional["Skill"]] = relationship(
        "Skill",
        back_populates="questions",
    )

    user_questions: Mapped[list["UserQuestion"]] = relationship(
        "UserQuestion",
        back_populates="question",
        cascade="all, delete-orphan",
    )


class UserQuestion(Base, TimestampMixin):
    __tablename__ = "user_questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[QuestionStatus] = mapped_column(
        SQLEnum(QuestionStatus, name="question_status"),
        nullable=False,
    )

    interview_question_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Relations ---
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="user_questions",
    )

    question: Mapped[Optional["Question"]] = relationship(
        "Question",
        back_populates="user_questions",
    )

    interview_question: Mapped[Optional["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="user_questions",
    )
