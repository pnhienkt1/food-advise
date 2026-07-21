import unicodedata

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

IS_SQLITE = settings.database_url.startswith("sqlite")


def strip_diacritics(value: str | None) -> str | None:
    """Remove Vietnamese diacritics for accent-insensitive matching (đ/Đ -> d/D)."""
    if value is None:
        return None
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


if IS_SQLITE:

    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_conn, _connection_record):  # pragma: no cover - driver glue
        dbapi_conn.create_function("unaccent", 1, strip_diacritics, deterministic=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
