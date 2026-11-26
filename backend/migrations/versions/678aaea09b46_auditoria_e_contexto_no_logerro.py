"""auditoria e contexto no logerro

Revision ID: 678aaea09b46
Revises: cc2afa2a5ad3
Create Date: 2026-11-26 11:40:52.230153

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "678aaea09b46"
down_revision: Union[str, Sequence[str], None] = "cc2afa2a5ad3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Nova ação auditada = nova migração alterando este CHECK.
ACOES = (
    "conta.cadastrar",
    "conta.entrar",
    "conta.entrar_falhou",
    "conta.excluir",
    "senha.solicitar",
    "senha.redefinir",
    "email.verificar",
    "cnpj.definir",
    "cnpj.remover",
    "dados.exportar",
)


def upgrade() -> None:
    op.create_table(
        "auditoria",
        sa.Column("idauditoria", sa.Integer(), nullable=False),
        sa.Column("idusuario", sa.Integer(), nullable=True),
        sa.Column("acao", sa.String(length=40), nullable=False),
        sa.Column("entidade", sa.String(length=60), nullable=True),
        sa.Column("identidade", sa.Integer(), nullable=True),
        sa.Column("dados", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("idrequisicao", sa.String(length=64), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "acao IN (" + ", ".join(f"'{a}'" for a in ACOES) + ")", name="ck_auditoria_acao"
        ),
        sa.ForeignKeyConstraint(
            ["idusuario"],
            ["public.usuario.idusuario"],
            name="fk_auditoria_idusuario",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("idauditoria"),
        schema="public",
    )
    op.create_index(
        "ix_auditoria_acao_data", "auditoria", ["acao", "criado_em"], schema="public"
    )
    op.create_index(
        "ix_auditoria_usuario_data", "auditoria", ["idusuario", "criado_em"], schema="public"
    )
    op.create_index(
        op.f("ix_public_auditoria_idrequisicao"), "auditoria", ["idrequisicao"], schema="public"
    )

    op.add_column(
        "logerro", sa.Column("idrequisicao", sa.String(length=64), nullable=True), schema="public"
    )
    op.add_column("logerro", sa.Column("ip", sa.String(length=45), nullable=True), schema="public")
    op.add_column("logerro", sa.Column("idusuario", sa.Integer(), nullable=True), schema="public")
    op.create_index(
        op.f("ix_public_logerro_idrequisicao"), "logerro", ["idrequisicao"], schema="public"
    )
    op.create_foreign_key(
        "fk_logerro_idusuario",
        "logerro",
        "usuario",
        ["idusuario"],
        ["idusuario"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_logerro_idusuario", "logerro", schema="public", type_="foreignkey")
    op.drop_index(op.f("ix_public_logerro_idrequisicao"), table_name="logerro", schema="public")
    op.drop_column("logerro", "idusuario", schema="public")
    op.drop_column("logerro", "ip", schema="public")
    op.drop_column("logerro", "idrequisicao", schema="public")
    op.drop_index(
        op.f("ix_public_auditoria_idrequisicao"), table_name="auditoria", schema="public"
    )
    op.drop_index("ix_auditoria_usuario_data", table_name="auditoria", schema="public")
    op.drop_index("ix_auditoria_acao_data", table_name="auditoria", schema="public")
    op.drop_table("auditoria", schema="public")
