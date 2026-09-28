from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora


class PrestadorPerfil(Base, SerializavelMixin):
    """Vitrine de quem presta serviço. 1:1 opcional com usuario: ser prestador é ter
    esta linha (não há coluna de papel)."""

    __tablename__ = "prestador_perfil"
    __table_args__ = (
        CheckConstraint(
            "preco_min IS NULL OR preco_max IS NULL OR preco_min <= preco_max",
            name="ck_prestador_perfil_faixa_preco",
        ),
        CheckConstraint(
            "(preco_min IS NULL OR preco_min >= 0) AND (preco_max IS NULL OR preco_max >= 0)",
            name="ck_prestador_perfil_preco_nao_negativo",
        ),
        {"schema": "public"},
    )

    idprestadorperfil = Column(Integer, primary_key=True)
    idusuario = Column(
        Integer,
        ForeignKey("public.usuario.idusuario", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    bio = Column(Text, nullable=True)
    preco_min = Column(Numeric(10, 2), nullable=True)
    preco_max = Column(Numeric(10, 2), nullable=True)
    disponibilidade = Column(String(120), nullable=True)
    # Só dígitos. Só é gravado depois de validado na BrasilAPI (RF-ID-07).
    cnpj = Column(String(14), nullable=True, unique=True)
    cnpj_validado_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, nullable=False, default=agora)
    atualizado_em = Column(DateTime, nullable=False, default=agora, onupdate=agora)

    usuario = relationship("Usuario", back_populates="prestador_perfil")
    servicos = relationship("Servico", secondary="public.prestador_servico", lazy="selectin")

    @property
    def servicos_ordenados(self) -> list:
        """Na ordem da taxonomia (categoria, depois serviço)."""
        return sorted(self.servicos, key=lambda s: (s.categoria.ordem, s.ordem))

    @property
    def categorias(self) -> list:
        """Categorias distintas dos serviços atendidos, na ordem da taxonomia."""
        vistas = {}
        for servico in self.servicos_ordenados:
            vistas.setdefault(servico.idcategoria, servico.categoria)
        return list(vistas.values())

    @property
    def cnpj_validado(self) -> bool:
        return self.cnpj is not None

    def __repr__(self):
        return (
            f"<PrestadorPerfil(idprestadorperfil={self.idprestadorperfil}, "
            f"idusuario={self.idusuario})>"
        )
