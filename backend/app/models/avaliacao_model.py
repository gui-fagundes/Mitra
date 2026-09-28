from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
)
from sqlalchemy.orm import backref, relationship

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora


class Avaliacao(Base, SerializavelMixin):
    """Avaliação pública do cliente sobre o prestador (RF-RE-01, RF-RE-02), com a
    resposta do prestador embutida (RF-RE-03).

    Só existe para contratação concluída (confirmação bilateral), uma por contratação.
    Autor e alvo vêm da contratação (cliente e prestador da conversa). Não é editável.
    """

    __tablename__ = "avaliacao"
    __table_args__ = (
        CheckConstraint("nota BETWEEN 1 AND 5", name="ck_avaliacao_nota"),
        {"schema": "public"},
    )

    idavaliacao = Column(Integer, primary_key=True)
    idcontratacao = Column(
        Integer,
        ForeignKey("public.contratacao.idcontratacao", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    nota = Column(SmallInteger, nullable=False)
    comentario = Column(Text, nullable=True)
    criado_em = Column(DateTime, nullable=False, default=agora)
    resposta = Column(Text, nullable=True)
    resposta_em = Column(DateTime, nullable=True)

    contratacao = relationship(
        "Contratacao",
        lazy="joined",
        backref=backref("avaliacao", uselist=False, lazy="selectin"),
    )

    def __repr__(self):
        return f"<Avaliacao(idavaliacao={self.idavaliacao}, nota={self.nota})>"
