"""Fixtures compartilhadas.

Estratégia:
- Um engine único apontando pro TEST_DATABASE_URL, criado uma vez por sessão de teste.
- Antes de tudo: drop_all + create_all (garante schema limpo, sem depender de Alembic).
- Cada teste roda dentro de uma transação que é revertida ao fim -> isolamento total,
  sem precisar TRUNCATE. FastAPI recebe uma sessão amarrada a essa transação via
  dependency_overrides.
"""

import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL não configurada no .env")

if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


@pytest.fixture(scope="session")
def engine():
    from app.config.database import Base
    from app.models import LogErro, Usuario  # noqa: F401  registra tabelas no metadata

    engine = create_engine(TEST_DATABASE_URL)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield engine

    engine.dispose()


@pytest.fixture()
def db_session(engine) -> Session:
    """Sessão amarrada a uma transação; rollback ao final do teste."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSession = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session) -> TestClient:
    """TestClient com get_db sobrescrito para usar a sessão transacional do teste."""
    from app.config.dependencies import get_db
    from main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
