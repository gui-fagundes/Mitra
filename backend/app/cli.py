"""Entry points expostos via [project.scripts]. Rode com `uv run <nome>`."""

import subprocess
import sys


def _run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def dev() -> int:
    """Migra o banco e sobe a API em modo dev (auto-reload)."""
    rc = migrate()
    if rc != 0:
        print("Migration falhou; abortando dev.")
        return rc

    return _run(["uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"])


def start() -> int:
    """Migra o banco e sobe a API em modo produção (múltiplos workers).

    Rodar `alembic upgrade head` antes dos workers evita que os N processos
    disputem o lock da tabela `alembic_version` no boot.
    """
    rc = migrate()
    if rc != 0:
        print("Migration falhou; abortando start.")
        return rc

    return _run(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"])


def migrate() -> int:
    """Aplica todas as migrations pendentes."""
    return _run(["alembic", "upgrade", "head"])


def rollback() -> int:
    """Reverte a última migration (alembic downgrade -1)."""
    return _run(["alembic", "downgrade", "-1"])


def makemigration() -> int:
    """Gera nova revisão autogenerate.

    Uso: uv run makemigration "mensagem" (o -m antes da mensagem é opcional)
    """
    args = [a for a in sys.argv[1:] if a != "-m"]
    if not args:
        print('Uso: uv run makemigration "descrição da migration"')
        return 1
    return _run(["alembic", "revision", "--autogenerate", "-m", " ".join(args)])


def test() -> int:
    """Roda pytest, repassando argumentos extras."""
    return _run(["pytest", *sys.argv[1:]])


def lint() -> int:
    """Roda ruff check no projeto."""
    return _run(["ruff", "check", "."])


def fmt() -> int:
    """Formata com ruff format."""
    return _run(["ruff", "format", "."])
