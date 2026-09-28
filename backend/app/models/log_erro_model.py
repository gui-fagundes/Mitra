from sqlalchemy import Column, DateTime, Integer, String, Text

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
    ocorrido_em = Column(DateTime, nullable=False, default=agora)

    def __repr__(self):
        return (
            f"<LogErro(idlogerro={self.idlogerro}, rota='{self.rota}', "
            f"metodo='{self.metodo}', ocorrido_em='{self.ocorrido_em}')>"
        )
