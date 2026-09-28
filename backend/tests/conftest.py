"""Fixtures compartilhadas.

Estratégia:
- Um engine único apontando pro TEST_DATABASE_URL, criado uma vez por sessão de teste.
- Antes de tudo: drop_all + create_all (garante schema limpo, sem depender do Alembic).
- Cada teste roda dentro de uma transação que é revertida ao fim -> isolamento total,
  sem precisar de TRUNCATE. O FastAPI recebe uma sessão amarrada a essa transação via
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
def sessao(engine) -> Session:
    """Sessão amarrada a uma transação; rollback ao final do teste."""
    conexao = engine.connect()
    transacao = conexao.begin()
    SessaoTeste = sessionmaker(bind=conexao, autocommit=False, autoflush=False)
    sessao = SessaoTeste()

    try:
        yield sessao
    finally:
        sessao.close()
        transacao.rollback()
        conexao.close()


@pytest.fixture()
def api(sessao) -> TestClient:
    """TestClient com obter_sessao sobrescrito para usar a sessão transacional do teste."""
    from app.config.dependencies import obter_sessao
    from main import app

    def _obter_sessao_teste():
        yield sessao

    app.dependency_overrides[obter_sessao] = _obter_sessao_teste
    with TestClient(app) as cliente_http:
        yield cliente_http
    app.dependency_overrides.clear()
