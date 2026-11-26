"""verificacao de email

Revision ID: cc2afa2a5ad3
Revises: 66853046eb55
Create Date: 2026-11-26 10:21:01.237713

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc2afa2a5ad3"
down_revision: Union[str, Sequence[str], None] = "66853046eb55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column("email_verificado_em", sa.DateTime(), nullable=True),
        schema="public",
    )
    # Contas criadas antes da verificação existir ficam como verificadas, para não
    # perderem de repente o acesso ao chat.
    op.execute("UPDATE public.usuario SET email_verificado_em = criado_em")


def downgrade() -> None:
    op.drop_column("usuario", "email_verificado_em", schema="public")
