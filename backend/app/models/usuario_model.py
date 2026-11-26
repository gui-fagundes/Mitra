from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, false, true
from sqlalchemy.orm import relationship

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
    telefone = Column(String(32), nullable=True)
    foto_url = Column(String(1024), nullable=True)
    idcidade = Column(
        Integer,
        ForeignKey("public.cidade.idcidade", ondelete="RESTRICT", name="fk_usuario_idcidade"),
        nullable=True,
        index=True,
    )
    # RF-DP-01. Nullable só por causa de contas criadas antes do aceite existir.
    aceite_termos_em = Column(DateTime, nullable=True)
    # RF-ID-01. Nulo até o usuário abrir o link enviado no cadastro.
    email_verificado_em = Column(DateTime, nullable=True)
    notificar_email = Column(Boolean, nullable=False, default=True, server_default=true())
    busca_somente_cnpj = Column(Boolean, nullable=False, default=False, server_default=false())
    # Atualizado em obter_usuario_logado (no máx. 1× a cada 5 min); alimenta o ranking.
    ultimo_acesso_em = Column(DateTime, nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, default=agora)

    cidade = relationship("Cidade", lazy="joined")
    prestador_perfil = relationship(
        "PrestadorPerfil",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def e_prestador(self) -> bool:
        return self.prestador_perfil is not None

    def __repr__(self):
        return f"<Usuario(idusuario={self.idusuario}, email='{self.email}')>"
