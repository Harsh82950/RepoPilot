import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RepositorySummary(Base):
    __tablename__ = "repository_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    tech_stack: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    architecture_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    important_modules: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    probable_entrypoints: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )