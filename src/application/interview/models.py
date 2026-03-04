from typing import Optional, List

from sqlalchemy import Integer, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.dbs.postgre import Base
from src.domain.base_model import TimestampMixin
from src.domain.value_objects import InterviewStatus


class InterviewSession(Base, TimestampMixin):
    __tablename__ = "interview_sessions"

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

    status: Mapped[InterviewStatus] = mapped_column(
        SQLEnum(InterviewStatus, name="interview_status"),
        nullable=False,
        default=InterviewStatus.ACTIVE,
    )

    current_main_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    total_main_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    # --- Relations ---
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="interview_sessions",
    )

    questions: Mapped[List["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class InterviewQuestion(Base, TimestampMixin):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=True,
    )

    question_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    is_followup: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    main_question_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        nullable=True,
    )

    followup_index: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # --- Relations ---
    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession",
        back_populates="questions",
    )

    question: Mapped[Optional["Question"]] = relationship(
        "Question",
    )

    main_question: Mapped[Optional["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        remote_side=[id],
    )

    user_questions: Mapped[List["UserQuestion"]] = relationship(
        "UserQuestion",
        back_populates="interview_question",
    )
