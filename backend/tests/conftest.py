from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, create_sqlite_engine, get_db
from app.main import app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    """API client that works against a fresh, empty SQLite file for each test."""
    engine = create_sqlite_engine(tmp_path / "test.db")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def get_test_db() -> Iterator[Session]:
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
