from sqlalchemy import Column, DateTime, Integer, String, Text

from app.config.database import Base
from app.models.base_model import ToDictMixin


class LogErro(Base, ToDictMixin):
    __tablename__ = "logerro"
    __table_args__ = {"schema": "public"}

    idlogerro = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(1024), nullable=False)
    metodo = Column(String(256), nullable=False)
    erro = Column(Text, nullable=False)
    datahora = Column(DateTime, nullable=False)

    def __repr__(self):
        return (
            f"<LogErro(idlogerro={self.idlogerro}, endpoint='{self.endpoint}', "
            f"metodo='{self.metodo}', datahora='{self.datahora}')>"
        )
