from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as orm


class TimestampMixin:
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True,
    )
