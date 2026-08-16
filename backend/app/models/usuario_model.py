from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.config.database import Base
from app.models.base_model import ToDictMixin
from app.utils.datetime_utils import get_now


class Usuario(Base, ToDictMixin):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "public"}

    idusuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    data_criacao = Column(DateTime, nullable=False, default=get_now)

    def __repr__(self):
        return f"<Usuario(idusuario={self.idusuario}, email='{self.email}')>"
