"""padroniza nomes em portugues

Renomeia colunas para o padrão do projeto (criação em `criado_em`, eventos em
`<evento>_em`, tudo em português). Escrita à mão: o autogenerate trataria o
rename como drop + add e perderia os dados.

Revision ID: a1c3e5f7b9d2
Revises: 7863c73c7a05
Create Date: 2026-09-27 00:00:00

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1c3e5f7b9d2'
down_revision: Union[str, Sequence[str], None] = '7863c73c7a05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('usuario', 'data_criacao', new_column_name='criado_em', schema='public')
    op.alter_column('logerro', 'endpoint', new_column_name='rota', schema='public')
    op.alter_column('logerro', 'datahora', new_column_name='ocorrido_em', schema='public')


def downgrade() -> None:
    op.alter_column('logerro', 'ocorrido_em', new_column_name='datahora', schema='public')
    op.alter_column('logerro', 'rota', new_column_name='endpoint', schema='public')
    op.alter_column('usuario', 'criado_em', new_column_name='data_criacao', schema='public')
