from sqlalchemy import Boolean, Column, Integer, String, true
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.models.base_model import SerializavelMixin


class Categoria(Base, SerializavelMixin):
    __tablename__ = "categoria"
    __table_args__ = {"schema": "public"}

    idcategoria = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False, unique=True)
    slug = Column(String(60), nullable=False, unique=True)
    icone = Column(String(60), nullable=False)
    ordem = Column(Integer, nullable=False, default=0, server_default="0")
    ativo = Column(Boolean, nullable=False, default=True, server_default=true())

    servicos = relationship("Servico", back_populates="categoria", order_by="Servico.ordem")
    # Somente leitura: o que a API pública lista.
    servicos_ativos = relationship(
        "Servico",
        primaryjoin="and_(Categoria.idcategoria == Servico.idcategoria, Servico.ativo.is_(True))",
        order_by="Servico.ordem",
        viewonly=True,
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Categoria(idcategoria={self.idcategoria}, slug='{self.slug}')>"
