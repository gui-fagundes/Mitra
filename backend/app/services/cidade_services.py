from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cidade_model import Cidade


def listar_ativas(db: Session) -> list[Cidade]:
    return db.query(Cidade).filter(Cidade.ativo.is_(True)).order_by(Cidade.uf, Cidade.nome).all()


def validar_cidade_ativa(idcidade: int, db: Session) -> Cidade:
    cidade = db.get(Cidade, idcidade)
    if not cidade or not cidade.ativo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Cidade inválida",
        )
    return cidade
