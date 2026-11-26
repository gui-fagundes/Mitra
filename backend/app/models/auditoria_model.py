from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora

# Ações sensíveis auditadas (RF-AD-02). De propósito só o que importa para segurança
# e LGPD: navegação, edição de perfil, chat e contratações já deixam histórico próprio.
CONTA_CADASTRAR = "conta.cadastrar"
CONTA_ENTRAR = "conta.entrar"
CONTA_ENTRAR_FALHOU = "conta.entrar_falhou"
CONTA_EXCLUIR = "conta.excluir"  # reservada para a exclusão de conta (RF-DP-03)
SENHA_SOLICITAR = "senha.solicitar"
SENHA_REDEFINIR = "senha.redefinir"
EMAIL_VERIFICAR = "email.verificar"
CNPJ_DEFINIR = "cnpj.definir"
CNPJ_REMOVER = "cnpj.remover"
DADOS_EXPORTAR = "dados.exportar"

ACOES = (
    CONTA_CADASTRAR,
    CONTA_ENTRAR,
    CONTA_ENTRAR_FALHOU,
    CONTA_EXCLUIR,
    SENHA_SOLICITAR,
    SENHA_REDEFINIR,
    EMAIL_VERIFICAR,
    CNPJ_DEFINIR,
    CNPJ_REMOVER,
    DADOS_EXPORTAR,
)


class Auditoria(Base, SerializavelMixin):
    """Registro de quem fez o quê e quando. A aplicação só insere; a remoção é
    exclusiva do expurgo por prazo de guarda (`uv run expurgar-registros`)."""

    __tablename__ = "auditoria"
    __table_args__ = (
        CheckConstraint(
            "acao IN (" + ", ".join(f"'{a}'" for a in ACOES) + ")",
            name="ck_auditoria_acao",
        ),
        Index("ix_auditoria_usuario_data", "idusuario", "criado_em"),
        Index("ix_auditoria_acao_data", "acao", "criado_em"),
        {"schema": "public"},
    )

    idauditoria = Column(Integer, primary_key=True)
    # Nulo em tentativas sem conta (login com e-mail inexistente) e depois que a
    # conta é excluída: o registro continua valendo, sem apontar para ninguém.
    idusuario = Column(
        Integer,
        ForeignKey("public.usuario.idusuario", ondelete="SET NULL", name="fk_auditoria_idusuario"),
        nullable=True,
    )
    acao = Column(String(40), nullable=False)
    # Registro afetado (tabela + id), quando há um.
    entidade = Column(String(60), nullable=True)
    identidade = Column(Integer, nullable=True)
    # O que mudou ({campo: [antes, depois]}) ou contexto mínimo. Nunca segredos.
    dados = Column(JSONB, nullable=True)
    ip = Column(String(45), nullable=True)
    idrequisicao = Column(String(64), nullable=True, index=True)
    criado_em = Column(DateTime, nullable=False, default=agora)

    def __repr__(self):
        return f"<Auditoria(idauditoria={self.idauditoria}, acao='{self.acao}')>"
