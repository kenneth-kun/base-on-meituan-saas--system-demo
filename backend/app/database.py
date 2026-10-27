from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .models.base import Base

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """建表。导入 models 以注册所有映射。"""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
