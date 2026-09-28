from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint, true

from app.config.database import Base
from app.models.base_model import SerializavelMixin


class Cidade(Base, SerializavelMixin):
    __tablename__ = "cidade"
    __table_args__ = (
        UniqueConstraint("nome", "uf", name="uq_cidade_nome_uf"),
        {"schema": "public"},
    )

    idcidade = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    uf = Column(String(2), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True, server_default=true())

    def __repr__(self):
        return f"<Cidade(idcidade={self.idcidade}, nome='{self.nome}', uf='{self.uf}')>"
