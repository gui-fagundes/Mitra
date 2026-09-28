from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao, obter_usuario_logado
from app.models.usuario_model import Usuario
from app.schemas.conversa_schema import (
    ConversaCriacao,
    ConversaResposta,
    MensagemEntrada,
    MensagemResposta,
    PaginaMensagensResposta,
)
from app.services import conversa_services

rotas_conversa = APIRouter(prefix="/conversas", tags=["Conversas"])


@rotas_conversa.post("", response_model=ConversaResposta, status_code=201)
def iniciar_conversa(
    corpo: ConversaCriacao,
    resposta: Response,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    """Inicia contato com um prestador. Se a conversa já existe, só envia a mensagem (200)."""
    conversa, criou = conversa_services.iniciar(usuario_logado, corpo.model_dump(), db)
    if not criou:
        resposta.status_code = 200
    return conversa


@rotas_conversa.get("", response_model=list[ConversaResposta])
def listar_conversas(
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return conversa_services.listar(usuario_logado, db)


@rotas_conversa.get("/{idconversa}", response_model=ConversaResposta)
def obter_conversa(
    idconversa: int,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return conversa_services.obter(usuario_logado, idconversa, db)


@rotas_conversa.get("/{idconversa}/mensagens", response_model=PaginaMensagensResposta)
def listar_mensagens(
    idconversa: int,
    antes_de: int | None = Query(default=None, description="Página anterior a esta mensagem"),
    depois_de: int | None = Query(default=None, description="Só as novas após esta mensagem"),
    limite: int = Query(default=50, ge=1, le=100),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return conversa_services.listar_mensagens(
        usuario_logado, idconversa, db, antes_de=antes_de, depois_de=depois_de, limite=limite
    )


@rotas_conversa.post("/{idconversa}/mensagens", response_model=MensagemResposta, status_code=201)
def enviar_mensagem(
    idconversa: int,
    corpo: MensagemEntrada,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return conversa_services.enviar(usuario_logado, idconversa, corpo.model_dump(), db)
