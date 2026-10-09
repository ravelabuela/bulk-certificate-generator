
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from database import Base


# Use an in-memory SQLite database for tests.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    # Create fresh tables before each test.
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Route API database requests to the test database.
    main.app.dependency_overrides[main.get_db] = override_get_db

    # Background processing also uses the test database.
    monkeypatch.setattr(main, "SessionLocal", TestingSessionLocal)

    yield

    # Remove test data and restore dependencies after each test.
    main.app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)