from fastapi import APIRouter, BackgroundTasks, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao, obter_usuario_logado
from app.models.usuario_model import Usuario
from app.schemas.usuario_schema import (
    Credenciais,
    EsqueciSenhaEntrada,
    RedefinirSenhaEntrada,
    UsuarioAtualizacao,
    UsuarioCriacao,
    UsuarioResposta,
)
from app.services import conta_services
from app.utils import email_utils
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


@rotas_conta.put("/foto", response_model=UsuarioResposta)
def trocar_foto(
    arquivo: UploadFile = File(description="Imagem JPG, PNG ou WebP de até 5 MB"),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return conta_services.trocar_foto(usuario_logado, arquivo, db)


@rotas_conta.delete("/foto", response_model=UsuarioResposta)
def remover_foto(
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return conta_services.remover_foto(usuario_logado, db)


@rotas_conta.post("/senha/esqueci", status_code=204)
def esqueci_senha(
    corpo: EsqueciSenhaEntrada,
    tarefas: BackgroundTasks,
    db: Session = Depends(obter_sessao),
):
    """Sempre 204, exista ou não conta com o e-mail (não revela quem é cadastrado)."""
    resultado = conta_services.solicitar_redefinicao_senha(corpo.model_dump(), db)
    if resultado:
        usuario, link = resultado
        assunto, texto = conta_services.montar_email_redefinicao(usuario, link)
        tarefas.add_task(email_utils.enviar_email, usuario.email, assunto, texto)


@rotas_conta.post("/senha/redefinir", status_code=204)
def redefinir_senha(corpo: RedefinirSenhaEntrada, db: Session = Depends(obter_sessao)):
    conta_services.redefinir_senha(corpo.model_dump(), db)
