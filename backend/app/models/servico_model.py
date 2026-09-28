from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint, true
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.models.base_model import SerializavelMixin


class Servico(Base, SerializavelMixin):
    __tablename__ = "servico"
    __table_args__ = (
        # "Móveis" existe em Conserto e em Artesanato: o slug é único só dentro da categoria.
        UniqueConstraint("idcategoria", "slug", name="uq_servico_categoria_slug"),
        {"schema": "public"},
    )

    idservico = Column(Integer, primary_key=True)
    idcategoria = Column(
        Integer,
        ForeignKey("public.categoria.idcategoria", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nome = Column(String(120), nullable=False)
    slug = Column(String(60), nullable=False)
    ordem = Column(Integer, nullable=False, default=0, server_default="0")
    ativo = Column(Boolean, nullable=False, default=True, server_default=true())

    categoria = relationship("Categoria", back_populates="servicos")

    def __repr__(self):
        return f"<Servico(idservico={self.idservico}, slug='{self.slug}')>"
