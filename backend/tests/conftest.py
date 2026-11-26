"""Fixtures compartilhadas.

Estratégia:
- Um engine único apontando pro TEST_DATABASE_URL, criado uma vez por sessão de teste.
- Antes de tudo: recria o schema `public` e aplica as migrations do Alembic até head.
  Assim o banco de teste tem os mesmos dados iniciais que as migrations gravam, e
  cada rodada também exercita as próprias migrations.
- Cada teste roda dentro de uma transação que é revertida ao fim -> isolamento total,
  sem precisar de TRUNCATE. O FastAPI recebe uma sessão amarrada a essa transação via
  dependency_overrides.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Os testes nunca falam com um servidor SMTP de verdade, mesmo com SMTP_HOST no .env
# (load_dotenv não sobrescreve variáveis já definidas). Quem precisa ver os e-mails
# usa a fixture `emails`.
os.environ["SMTP_HOST"] = ""

load_dotenv()

# Uploads dos testes vão para uma pasta temporária. Precisa ser definido antes de
# qualquer import de `app` (constants lê UPLOADS_DIR no import).
DIR_UPLOADS_TESTE = Path(tempfile.mkdtemp(prefix="mitra_uploads_teste_"))
os.environ["UPLOADS_DIR"] = str(DIR_UPLOADS_TESTE)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL não configurada no .env")

if TEST_DATABASE_URL.startswith("postgresql://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


DIR_BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def _limpar_uploads_de_teste():
    yield
    shutil.rmtree(DIR_UPLOADS_TESTE, ignore_errors=True)


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)

    with engine.begin() as conexao:
        conexao.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
        conexao.exec_driver_sql("CREATE SCHEMA public")

    cfg = Config(str(DIR_BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(DIR_BACKEND / "migrations"))
    with engine.begin() as conexao:
        cfg.attributes["connection"] = conexao
        command.upgrade(cfg, "head")

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


@pytest.fixture()
def emails(monkeypatch) -> list[dict]:
    """Captura os e-mails que a API mandaria (para, assunto, corpo), na ordem."""
    from app.utils import email_utils

    enviados: list[dict] = []

    async def _capturar(para, assunto, corpo_texto, corpo_html=None):
        enviados.append({"para": para, "assunto": assunto, "corpo": corpo_texto})

    monkeypatch.setattr(email_utils, "enviar_email", _capturar)
    return enviados
