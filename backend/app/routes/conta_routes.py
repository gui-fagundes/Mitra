from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao, obter_usuario_logado
from app.models.usuario_model import Usuario
from app.schemas.usuario_schema import (
    Credenciais,
    UsuarioAtualizacao,
    UsuarioCriacao,
    UsuarioResposta,
)
from app.services import conta_services
from app.utils.cookie_utils import apagar_cookie_sessao, gravar_cookie_sessao

rotas_conta = APIRouter(prefix="/conta", tags=["Conta"])


@rotas_conta.post("/cadastro", response_model=UsuarioResposta)
def cadastrar(corpo: UsuarioCriacao, resposta: Response, db: Session = Depends(obter_sessao)):
    usuario = conta_services.cadastrar(corpo.model_dump(), db)
    gravar_cookie_sessao(resposta, conta_services.gerar_token(usuario))
    return usuario


@rotas_conta.post("/entrar", response_model=UsuarioResposta)
def entrar(corpo: Credenciais, resposta: Response, db: Session = Depends(obter_sessao)):
    usuario = conta_services.entrar(corpo.model_dump(), db)
    gravar_cookie_sessao(resposta, conta_services.gerar_token(usuario))
    return usuario


@rotas_conta.post("/sair", status_code=204)
def sair(resposta: Response):
    apagar_cookie_sessao(resposta)


@rotas_conta.get("", response_model=UsuarioResposta)
def obter_conta(usuario_logado: Usuario = Depends(obter_usuario_logado)):
    return usuario_logado


@rotas_conta.patch("", response_model=UsuarioResposta)
def atualizar_conta(
    corpo: UsuarioAtualizacao,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return conta_services.atualizar(usuario_logado, corpo.model_dump(exclude_unset=True), db)
