"""Comandos expostos via [project.scripts]. Rode com `uv run <comando>`."""

import subprocess
import sys


def _executar(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def dev() -> int:
    """Migra o banco e sobe a API em modo desenvolvimento (auto-reload)."""
    rc = migrar()
    if rc != 0:
        print("Migração falhou; abortando dev.")
        return rc

    return _executar(["uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"])


def producao() -> int:
    """Migra o banco e sobe a API em modo produção (múltiplos workers).

    Rodar `alembic upgrade head` antes dos workers evita que os N processos
    disputem o lock da tabela `alembic_version` no boot.
    """
    rc = migrar()
    if rc != 0:
        print("Migração falhou; abortando producao.")
        return rc

    return _executar(
        ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
    )


def migrar() -> int:
    """Aplica todas as migrações pendentes."""
    return _executar(["alembic", "upgrade", "head"])


def reverter() -> int:
    """Reverte a última migração (alembic downgrade -1)."""
    return _executar(["alembic", "downgrade", "-1"])


def criar_migracao() -> int:
    """Gera nova revisão autogenerate. Uso: uv run criar-migracao "descrição" """
    args = [a for a in sys.argv[1:] if a != "-m"]
    if not args:
        print('Uso: uv run criar-migracao "descrição da migração"')
        return 1
    return _executar(["alembic", "revision", "--autogenerate", "-m", " ".join(args)])


def expurgar_registros() -> int:
    """Apaga auditoria e log de erros que passaram do prazo de guarda."""
    from app.config.constants import DIAS_RETENCAO_AUDITORIA, DIAS_RETENCAO_LOGERRO
    from app.config.database import SessaoLocal
    from app.services.auditoria_services import expurgar

    db = SessaoLocal()
    try:
        auditoria, logerro = expurgar(db)
    finally:
        db.close()
    print(
        f"Removidos {auditoria} registros de auditoria (> {DIAS_RETENCAO_AUDITORIA} dias) "
        f"e {logerro} de log de erros (> {DIAS_RETENCAO_LOGERRO} dias)."
    )
    return 0


def testar() -> int:
    """Roda pytest, repassando argumentos extras."""
    return _executar(["pytest", *sys.argv[1:]])


def verificar() -> int:
    """Roda ruff check (lint) no projeto."""
    return _executar(["ruff", "check", "."])


def formatar() -> int:
    """Formata com ruff format."""
    return _executar(["ruff", "format", "."])
