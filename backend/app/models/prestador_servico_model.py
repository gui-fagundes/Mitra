from sqlalchemy import Column, ForeignKey, Integer

from app.config.database import Base
from app.models.base_model import SerializavelMixin


class PrestadorServico(Base, SerializavelMixin):
    """Serviços que um prestador atende (RF-CA-02). O limite de 3 é validado no
    service, não no banco, para poder mudar sem migration."""

    __tablename__ = "prestador_servico"
    __table_args__ = {"schema": "public"}

    idprestadorperfil = Column(
        Integer,
        ForeignKey("public.prestador_perfil.idprestadorperfil", ondelete="CASCADE"),
        primary_key=True,
    )
    idservico = Column(
        Integer,
        ForeignKey("public.servico.idservico", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    )
