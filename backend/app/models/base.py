from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def now() -> datetime:
    """骨架阶段用本地时间；生产建议统一 UTC。"""
    return datetime.now()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
