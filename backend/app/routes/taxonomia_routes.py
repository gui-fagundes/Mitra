from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao
from app.schemas.taxonomia_schema import CategoriaResposta, ServicoResposta
from app.services import taxonomia_services

rotas_taxonomia = APIRouter(tags=["Taxonomia"])


@rotas_taxonomia.get("/categorias", response_model=list[CategoriaResposta])
def listar_categorias(db: Session = Depends(obter_sessao)):
    """RF-CA-01: categorias ativas em ordem, com seus serviços aninhados."""
    return taxonomia_services.listar_categorias(db)


@rotas_taxonomia.get("/servicos", response_model=list[ServicoResposta])
def listar_servicos(categoria: str | None = None, db: Session = Depends(obter_sessao)):
    """Serviços de uma categoria (pelo slug) ou de todas."""
    return taxonomia_services.listar_servicos(db, categoria)
