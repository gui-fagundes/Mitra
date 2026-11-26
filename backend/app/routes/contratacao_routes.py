from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao, obter_usuario_logado, obter_usuario_verificado
from app.models.usuario_model import Usuario
from app.schemas.contratacao_schema import (
    CancelamentoEntrada,
    ConclusaoEntrada,
    ContratacaoResposta,
    Estado,
    PropostaAtualizacao,
    PropostaEntrada,
)
from app.services import contratacao_services, notificacao_services

rotas_contratacao = APIRouter(prefix="/contratacoes", tags=["Contratações"])
# A proposta nasce dentro de uma conversa.
rotas_contratacao_da_conversa = APIRouter(prefix="/conversas", tags=["Contratações"])


@rotas_contratacao_da_conversa.post(
    "/{idconversa}/contratacoes", response_model=ContratacaoResposta, status_code=201
)
def propor(
    idconversa: int,
    corpo: PropostaEntrada,
    tarefas: BackgroundTasks,
    usuario_logado: Usuario = Depends(obter_usuario_verificado),
    db: Session = Depends(obter_sessao),
):
    """Cliente ou prestador propõe a prestação (RF-CO-01). 409 se já há uma aberta."""
    resultado = contratacao_services.propor(usuario_logado, idconversa, corpo.model_dump(), db)
    notificacao_services.agendar(tarefas, db)
    return resultado


@rotas_contratacao_da_conversa.get(
    "/{idconversa}/contratacoes", response_model=list[ContratacaoResposta]
)
def listar_da_conversa(
    idconversa: int,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return contratacao_services.listar_da_conversa(usuario_logado, idconversa, db)


@rotas_contratacao.get("", response_model=list[ContratacaoResposta])
def listar_minhas(
    papel: Literal["cliente", "prestador", "todos"] = "todos",
    estado: Estado | None = None,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return contratacao_services.listar_minhas(usuario_logado, db, papel=papel, estado=estado)


@rotas_contratacao.get("/{idcontratacao}", response_model=ContratacaoResposta)
def obter(
    idcontratacao: int,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return contratacao_services.obter(usuario_logado, idcontratacao, db)


@rotas_contratacao.patch("/{idcontratacao}", response_model=ContratacaoResposta)
def editar_proposta(
    idcontratacao: int,
    corpo: PropostaAtualizacao,
    tarefas: BackgroundTasks,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    resultado = contratacao_services.editar_proposta(
        usuario_logado, idcontratacao, corpo.model_dump(exclude_unset=True), db
    )
    notificacao_services.agendar(tarefas, db)
    return resultado


@rotas_contratacao.post("/{idcontratacao}/aceitar", response_model=ContratacaoResposta)
def aceitar(
    idcontratacao: int,
    tarefas: BackgroundTasks,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    resultado = contratacao_services.aceitar(usuario_logado, idcontratacao, db)
    notificacao_services.agendar(tarefas, db)
    return resultado


@rotas_contratacao.post("/{idcontratacao}/concluir", response_model=ContratacaoResposta)
def confirmar_conclusao(
    idcontratacao: int,
    corpo: ConclusaoEntrada,
    tarefas: BackgroundTasks,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    """Confirmação bilateral de conclusão (RF-CO-04), com o preço cobrado."""
    resultado = contratacao_services.confirmar_conclusao(
        usuario_logado, idcontratacao, corpo.model_dump(exclude_unset=True), db
    )
    notificacao_services.agendar(tarefas, db)
    return resultado


@rotas_contratacao.post("/{idcontratacao}/cancelar", response_model=ContratacaoResposta)
def cancelar(
    idcontratacao: int,
    corpo: CancelamentoEntrada,
    tarefas: BackgroundTasks,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    resultado = contratacao_services.cancelar(usuario_logado, idcontratacao, corpo.model_dump(), db)
    notificacao_services.agendar(tarefas, db)
    return resultado
