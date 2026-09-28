from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora


class Mensagem(Base, SerializavelMixin):
    """Mensagem de uma conversa. `tipo` "evento" registra automaticamente o que
    aconteceu com uma proposta (enviada, aceita, concluída, cancelada)."""

    __tablename__ = "mensagem"
    __table_args__ = (
        CheckConstraint("tipo IN ('texto', 'evento')", name="ck_mensagem_tipo"),
        # Histórico paginado por id dentro da conversa.
        Index("ix_mensagem_conversa_id", "idconversa", "idmensagem"),
        {"schema": "public"},
    )

    idmensagem = Column(Integer, primary_key=True)
    idconversa = Column(
        Integer,
        ForeignKey("public.conversa.idconversa", ondelete="CASCADE"),
        nullable=False,
    )
    idautor = Column(
        Integer, ForeignKey("public.usuario.idusuario", ondelete="RESTRICT"), nullable=False
    )
    tipo = Column(String(10), nullable=False, default="texto", server_default="texto")
    texto = Column(Text, nullable=False)
    criado_em = Column(DateTime, nullable=False, default=agora)

    def __repr__(self):
        return f"<Mensagem(idmensagem={self.idmensagem}, idconversa={self.idconversa})>"
