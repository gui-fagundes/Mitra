from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora

ESTADOS_ABERTOS = ("proposta", "combinado")


class Contratacao(Base, SerializavelMixin):
    """Prestação de serviço combinada dentro de uma conversa (RF-CO-01, RF-CO-04).

    proposta → (aceite dos dois) → combinado → (conclusão confirmada pelos dois,
    com o preço cobrado) → concluido. Proposta ou combinado podem ser cancelados.
    Cliente e prestador vêm da conversa.
    """

    __tablename__ = "contratacao"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('proposta', 'combinado', 'concluido', 'cancelado')",
            name="ck_contratacao_estado",
        ),
        CheckConstraint(
            "(valor_estimado IS NULL OR valor_estimado >= 0)"
            " AND (valor_final IS NULL OR valor_final >= 0)",
            name="ck_contratacao_valores_nao_negativos",
        ),
        # No máximo uma contratação em andamento por conversa.
        Index(
            "uq_contratacao_aberta_por_conversa",
            "idconversa",
            unique=True,
            postgresql_where=text("estado IN ('proposta', 'combinado')"),
        ),
        Index("ix_contratacao_conversa", "idconversa"),
        {"schema": "public"},
    )

    idcontratacao = Column(Integer, primary_key=True)
    idconversa = Column(
        Integer,
        ForeignKey("public.conversa.idconversa", ondelete="RESTRICT"),
        nullable=False,
    )
    # Quem fez a proposta (cliente ou prestador).
    idproponente = Column(
        Integer, ForeignKey("public.usuario.idusuario", ondelete="RESTRICT"), nullable=False
    )

    # Proposta
    idservico = Column(
        Integer, ForeignKey("public.servico.idservico", ondelete="RESTRICT"), nullable=False
    )
    descricao = Column(Text, nullable=False)
    local = Column(String(255), nullable=True)
    data_prevista = Column(Date, nullable=True)
    # Orçamento do prestador ou budget do cliente.
    valor_estimado = Column(Numeric(10, 2), nullable=True)

    estado = Column(String(12), nullable=False, default="proposta", server_default="proposta")

    # Plano: aceite bilateral da versão atual da proposta.
    aceite_cliente_em = Column(DateTime, nullable=True)
    aceite_prestador_em = Column(DateTime, nullable=True)
    combinado_em = Column(DateTime, nullable=True)

    # Conclusão: os dois confirmam que foi feito e o preço cobrado.
    valor_final = Column(Numeric(10, 2), nullable=True)
    conclusao_cliente_em = Column(DateTime, nullable=True)
    conclusao_prestador_em = Column(DateTime, nullable=True)
    concluido_em = Column(DateTime, nullable=True)

    cancelado_em = Column(DateTime, nullable=True)
    idcancelado_por = Column(
        Integer, ForeignKey("public.usuario.idusuario", ondelete="RESTRICT"), nullable=True
    )
    motivo_cancelamento = Column(String(255), nullable=True)

    criado_em = Column(DateTime, nullable=False, default=agora)
    atualizado_em = Column(DateTime, nullable=False, default=agora, onupdate=agora)

    conversa = relationship("Conversa", lazy="joined")
    servico = relationship("Servico", lazy="joined")

    def papel_de(self, idusuario: int) -> str:
        return "cliente" if idusuario == self.conversa.idcliente else "prestador"

    def __repr__(self):
        return f"<Contratacao(idcontratacao={self.idcontratacao}, estado='{self.estado}')>"
