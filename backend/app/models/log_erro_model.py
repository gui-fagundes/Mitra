from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.config.database import Base
from app.models.base_model import SerializavelMixin
from app.utils.data_utils import agora


class LogErro(Base, SerializavelMixin):
    __tablename__ = "logerro"
    __table_args__ = {"schema": "public"}

    idlogerro = Column(Integer, primary_key=True, index=True)
    rota = Column(String(1024), nullable=False)
    metodo = Column(String(256), nullable=False)
    erro = Column(Text, nullable=False)
    # Liga o erro à requisição (mesmo idrequisicao da auditoria) e a quem a fez.
    idrequisicao = Column(String(64), nullable=True, index=True)
    ip = Column(String(45), nullable=True)
    idusuario = Column(
        Integer,
        ForeignKey("public.usuario.idusuario", ondelete="SET NULL", name="fk_logerro_idusuario"),
        nullable=True,
    )
    ocorrido_em = Column(DateTime, nullable=False, default=agora)

    def __repr__(self):
        return (
            f"<LogErro(idlogerro={self.idlogerro}, rota='{self.rota}', "
            f"metodo='{self.metodo}', ocorrido_em='{self.ocorrido_em}')>"
        )
