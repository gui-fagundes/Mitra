from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora


class PrestadorPortfolio(Base, SerializavelMixin):
    """Imagem do portfólio do prestador (RF-ID-04). Limite de 10 validado no service."""

    __tablename__ = "prestador_portfolio"
    __table_args__ = {"schema": "public"}

    idprestadorportfolio = Column(Integer, primary_key=True)
    idprestadorperfil = Column(
        Integer,
        ForeignKey("public.prestador_perfil.idprestadorperfil", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Caminho público devolvido por arquivo_utils.salvar_imagem ("/arquivos/portfolio/…").
    imagem_url = Column(String(1024), nullable=False)
    legenda = Column(String(255), nullable=True)
    # Posição na galeria, 0..n-1; reordenável.
    ordem = Column(Integer, nullable=False, default=0)
    criado_em = Column(DateTime, nullable=False, default=agora)

    def __repr__(self):
        return (
            f"<PrestadorPortfolio(idprestadorportfolio={self.idprestadorportfolio}, "
            f"ordem={self.ordem})>"
        )
