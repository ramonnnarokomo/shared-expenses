from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_PATH = Path(__file__).resolve().parent.parent / "shared_expenses.db"


class Base(DeclarativeBase):
    pass


def create_sqlite_engine(path: Path) -> Engine:
    """Creates an engine for a SQLite file with foreign key checks turned on."""
    # FastAPI runs sync endpoints in a thread pool, so a connection may be used from another thread.
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})

    # SQLite ignores foreign keys unless this pragma is set on every connection.
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = create_sqlite_engine(DATABASE_PATH)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one database session per request."""
    with SessionLocal() as session:
        yield session
