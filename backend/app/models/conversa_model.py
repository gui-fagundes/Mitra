from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora


class Conversa(Base, SerializavelMixin):
    """Chat entre quem procura um serviço e um prestador (RF-CO-02).

    Independente da contratação: uma por par, com histórico contínuo. As propostas
    de serviço nascem dentro dela.
    """

    __tablename__ = "conversa"
    __table_args__ = (
        UniqueConstraint("idcliente", "idprestador", name="uq_conversa_par"),
        CheckConstraint("idcliente <> idprestador", name="ck_conversa_participantes_distintos"),
        # Listagem "minhas conversas", da mais recente para a mais antiga.
        Index("ix_conversa_cliente_atualizado", "idcliente", "atualizado_em"),
        Index("ix_conversa_prestador_atualizado", "idprestador", "atualizado_em"),
        {"schema": "public"},
    )

    idconversa = Column(Integer, primary_key=True)
    # Quem iniciou o contato.
    idcliente = Column(
        Integer, ForeignKey("public.usuario.idusuario", ondelete="RESTRICT"), nullable=False
    )
    # Dono do perfil de prestador procurado.
    idprestador = Column(
        Integer, ForeignKey("public.usuario.idusuario", ondelete="RESTRICT"), nullable=False
    )
    criado_em = Column(DateTime, nullable=False, default=agora)
    # Atualizado a cada mensagem: ordena a lista de conversas.
    atualizado_em = Column(DateTime, nullable=False, default=agora)

    cliente = relationship("Usuario", foreign_keys=[idcliente], lazy="joined")
    prestador = relationship("Usuario", foreign_keys=[idprestador], lazy="joined")

    def participa(self, idusuario: int) -> bool:
        return idusuario in (self.idcliente, self.idprestador)

    def outra_parte(self, idusuario: int):
        return self.prestador if idusuario == self.idcliente else self.cliente

    def __repr__(self):
        return (
            f"<Conversa(idconversa={self.idconversa}, idcliente={self.idcliente}, "
            f"idprestador={self.idprestador})>"
        )
