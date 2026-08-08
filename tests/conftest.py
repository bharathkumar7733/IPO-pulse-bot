import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Base
from app.db.seed import seed_db

@pytest.fixture(scope="function")
def db_engine():
    """Create a shared in-memory SQLite engine with StaticPool for multi-threaded testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a clean DB session for each test function."""
    Session = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()

@pytest.fixture(scope="function")
def seeded_db(db_engine, db_session):
    """Provide a database session pre-populated with seed data."""
    seed_db(db_session)
    return db_session
