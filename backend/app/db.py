from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


def make_engine(settings: Settings | None = None):
    settings = settings or get_settings()
    if not settings.database_url:
        raise RuntimeError("Missing required setting: DATABASE_URL")
    return create_engine(settings.database_url, pool_pre_ping=True)


def make_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(settings), expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    session_factory = make_session_factory()
    with session_factory() as session:
        yield session
