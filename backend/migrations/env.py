import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from alembic.operations import ops
from sqlalchemy import engine_from_config, pool

# Garante que o pacote `app` fique importável quando o Alembic roda a partir do backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: E402,F401  (registra todas as tabelas no metadata)
from app.config.database import DATABASE_URL, Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = Base.metadata


def _chave_fk(operacao) -> tuple | None:
    """Identifica uma FK por tabela, colunas, alvo e ações — ignorando o schema."""
    if isinstance(operacao, ops.CreateForeignKeyOp):
        fk = operacao.to_constraint()
    elif isinstance(operacao, ops.DropConstraintOp) and operacao.constraint_type == "foreignkey":
        if operacao._reverse is None:
            return None
        fk = operacao.to_constraint()
    else:
        return None
    # target_fullname vem como "schema.tabela.coluna" ou "tabela.coluna": fica só o fim.
    colunas = tuple((e.parent.name, *e.target_fullname.rsplit(".", 2)[-2:]) for e in fk.elements)
    return (fk.table.name, colunas, fk.ondelete, fk.onupdate)


def _descartar_fks_so_de_schema(container) -> None:
    """Remove pares "drop FK + create FK" idênticos a menos do schema.

    Todas as tabelas declaram schema="public". O Postgres reflete FKs sem o schema
    quando ele está no search_path, e o autogenerate passa a ver toda FK como
    diferente do model. Aqui descartamos só esse falso positivo; FK que muda de
    fato (colunas, alvo, ON DELETE) continua aparecendo.
    """
    novas = []
    for operacao in container.ops:
        if isinstance(operacao, ops.ModifyTableOps):
            removidas = {_chave_fk(o) for o in operacao.ops if isinstance(o, ops.DropConstraintOp)}
            criadas = {_chave_fk(o) for o in operacao.ops if isinstance(o, ops.CreateForeignKeyOp)}
            iguais = (removidas & criadas) - {None}
            operacao.ops = [o for o in operacao.ops if _chave_fk(o) not in iguais]
            if not operacao.ops:
                continue
        novas.append(operacao)
    container.ops = novas


def _processar_diretivas(_contexto, _revisao, diretivas) -> None:
    for script in diretivas:
        for operacoes in (*script.upgrade_ops_list, *script.downgrade_ops_list):
            _descartar_fks_so_de_schema(operacoes)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _executar(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=_processar_diretivas,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Quem chama pode fornecer a conexão (ex.: testes migrando o banco de teste).
    conexao_fornecida = config.attributes.get("connection")
    if conexao_fornecida is not None:
        _executar(conexao_fornecida)
        return

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _executar(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
