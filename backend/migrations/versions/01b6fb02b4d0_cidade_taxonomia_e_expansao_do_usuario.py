"""cidade, taxonomia e expansao do usuario

Etapa "Conta, cidade e taxonomia" (docs/backend-plan.md): cria `cidade`, `categoria` e `servico` já com os
dados iniciais do piloto, e expande `usuario` com contato, cidade, aceite dos
termos (RF-DP-01), preferências e último acesso.

Revision ID: 01b6fb02b4d0
Revises: a1c3e5f7b9d2
Create Date: 2026-09-27 23:30:46.414540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01b6fb02b4d0'
down_revision: Union[str, Sequence[str], None] = 'a1c3e5f7b9d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CIDADES = [
    {'nome': 'Rio Grande', 'uf': 'RS'},
]

# (nome, slug, icone Font Awesome, [(nome do serviço, slug), ...]) — RF-CA-01
TAXONOMIA = [
    ('Conserto', 'conserto', 'fa-wrench', [
        ('Eletroeletrônicos', 'eletroeletronicos'),
        ('Roupas / vestimenta', 'roupas-vestimenta'),
        ('Móveis', 'moveis'),
        ('Construção / manutenção', 'construcao-manutencao'),
    ]),
    ('Educação', 'educacao', 'fa-graduation-cap', [
        ('Aulas particulares', 'aulas-particulares'),
        ('Personal trainer', 'personal-trainer'),
        ('Treinamentos', 'treinamentos'),
    ]),
    ('Pets', 'pets', 'fa-paw', [
        ('Adestramento', 'adestramento'),
        ('Banho / tosa', 'banho-tosa'),
        ('Cuidador', 'cuidador'),
        ('Hospedagem', 'hospedagem'),
    ]),
    ('Entretenimento', 'entretenimento', 'fa-music', [
        ('Música ao vivo', 'musica-ao-vivo'),
        ('Recreação infantil', 'recreacao-infantil'),
        ('Organização de festas', 'organizacao-de-festas'),
    ]),
    ('Artesanato', 'artesanato', 'fa-paint-brush', [
        ('Móveis sob medida', 'moveis-sob-medida'),
        ('Roupas / acessórios', 'roupas-acessorios'),
        ('Decoração', 'decoracao'),
    ]),
]


def upgrade() -> None:
    cidade = op.create_table('cidade',
    sa.Column('idcidade', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('uf', sa.String(length=2), nullable=False),
    sa.Column('ativo', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.PrimaryKeyConstraint('idcidade'),
    sa.UniqueConstraint('nome', 'uf', name='uq_cidade_nome_uf'),
    schema='public'
    )
    categoria = op.create_table('categoria',
    sa.Column('idcategoria', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('slug', sa.String(length=60), nullable=False),
    sa.Column('icone', sa.String(length=60), nullable=False),
    sa.Column('ordem', sa.Integer(), server_default='0', nullable=False),
    sa.Column('ativo', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.PrimaryKeyConstraint('idcategoria'),
    sa.UniqueConstraint('nome'),
    sa.UniqueConstraint('slug'),
    schema='public'
    )
    servico = op.create_table('servico',
    sa.Column('idservico', sa.Integer(), nullable=False),
    sa.Column('idcategoria', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('slug', sa.String(length=60), nullable=False),
    sa.Column('ordem', sa.Integer(), server_default='0', nullable=False),
    sa.Column('ativo', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.ForeignKeyConstraint(['idcategoria'], ['public.categoria.idcategoria'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('idservico'),
    sa.UniqueConstraint('idcategoria', 'slug', name='uq_servico_categoria_slug'),
    schema='public'
    )
    op.create_index(op.f('ix_public_servico_idcategoria'), 'servico', ['idcategoria'], unique=False, schema='public')

    op.add_column('usuario', sa.Column('telefone', sa.String(length=32), nullable=True), schema='public')
    op.add_column('usuario', sa.Column('foto_url', sa.String(length=1024), nullable=True), schema='public')
    op.add_column('usuario', sa.Column('idcidade', sa.Integer(), nullable=True), schema='public')
    op.add_column('usuario', sa.Column('aceite_termos_em', sa.DateTime(), nullable=True), schema='public')
    op.add_column('usuario', sa.Column('notificar_email', sa.Boolean(), server_default=sa.text('true'), nullable=False), schema='public')
    op.add_column('usuario', sa.Column('busca_somente_cnpj', sa.Boolean(), server_default=sa.text('false'), nullable=False), schema='public')
    op.add_column('usuario', sa.Column('ultimo_acesso_em', sa.DateTime(), nullable=True), schema='public')
    op.create_index(op.f('ix_public_usuario_idcidade'), 'usuario', ['idcidade'], unique=False, schema='public')
    op.create_foreign_key('fk_usuario_idcidade', 'usuario', 'cidade', ['idcidade'], ['idcidade'], source_schema='public', referent_schema='public', ondelete='RESTRICT')

    # Dados iniciais do piloto
    op.bulk_insert(cidade, CIDADES)
    op.bulk_insert(categoria, [
        {'nome': nome, 'slug': slug, 'icone': icone, 'ordem': ordem}
        for ordem, (nome, slug, icone, _) in enumerate(TAXONOMIA, start=1)
    ])
    ids_categoria = dict(
        op.get_bind().execute(sa.text('SELECT slug, idcategoria FROM public.categoria')).all()
    )
    op.bulk_insert(servico, [
        {'idcategoria': ids_categoria[slug_categoria], 'nome': nome, 'slug': slug, 'ordem': ordem}
        for _, slug_categoria, _, servicos in TAXONOMIA
        for ordem, (nome, slug) in enumerate(servicos, start=1)
    ])


def downgrade() -> None:
    op.drop_constraint('fk_usuario_idcidade', 'usuario', schema='public', type_='foreignkey')
    op.drop_index(op.f('ix_public_usuario_idcidade'), table_name='usuario', schema='public')
    op.drop_column('usuario', 'ultimo_acesso_em', schema='public')
    op.drop_column('usuario', 'busca_somente_cnpj', schema='public')
    op.drop_column('usuario', 'notificar_email', schema='public')
    op.drop_column('usuario', 'aceite_termos_em', schema='public')
    op.drop_column('usuario', 'idcidade', schema='public')
    op.drop_column('usuario', 'foto_url', schema='public')
    op.drop_column('usuario', 'telefone', schema='public')
    op.drop_index(op.f('ix_public_servico_idcategoria'), table_name='servico', schema='public')
    op.drop_table('servico', schema='public')
    op.drop_table('categoria', schema='public')
    op.drop_table('cidade', schema='public')
