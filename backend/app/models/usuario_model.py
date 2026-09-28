from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora


class Usuario(Base, SerializavelMixin):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "public"}

    idusuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, default=agora)

    def __repr__(self):
        return f"<Usuario(idusuario={self.idusuario}, email='{self.email}')>"
