from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao
from app.schemas.cidade_schema import CidadeResposta
from app.services import cidade_services

rotas_cidade = APIRouter(prefix="/cidades", tags=["Cidades"])


@rotas_cidade.get("", response_model=list[CidadeResposta])
def listar_cidades(db: Session = Depends(obter_sessao)):
    return cidade_services.listar_ativas(db)
