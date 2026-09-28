from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao, obter_usuario_logado
from app.models.usuario_model import Usuario
from app.schemas.avaliacao_schema import (
    AvaliacaoEntrada,
    AvaliacaoResposta,
    PaginaAvaliacoesResposta,
    RespostaEntrada,
)
from app.services import avaliacao_services

rotas_avaliacao = APIRouter(tags=["Avaliações"])


@rotas_avaliacao.post(
    "/contratacoes/{idcontratacao}/avaliacao", response_model=AvaliacaoResposta, status_code=201
)
def avaliar(
    idcontratacao: int,
    corpo: AvaliacaoEntrada,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    """RF-RE-01/02: só o cliente, só com a contratação concluída, até 30 dias depois."""
    return avaliacao_services.avaliar(usuario_logado, idcontratacao, corpo.model_dump(), db)


@rotas_avaliacao.post("/avaliacoes/{idavaliacao}/resposta", response_model=AvaliacaoResposta)
def responder(
    idavaliacao: int,
    corpo: RespostaEntrada,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    """RF-RE-03: resposta pública do prestador avaliado, uma vez."""
    return avaliacao_services.responder(usuario_logado, idavaliacao, corpo.model_dump(), db)


@rotas_avaliacao.get("/prestadores/{idusuario}/avaliacoes", response_model=PaginaAvaliacoesResposta)
def listar_do_prestador(
    idusuario: int,
    limite: int = Query(default=20, ge=1, le=50),
    deslocamento: int = Query(default=0, ge=0),
    db: Session = Depends(obter_sessao),
):
    """Lista pública, da mais recente para a mais antiga."""
    return avaliacao_services.listar_do_prestador(idusuario, db, limite, deslocamento)
