from datetime import timedelta

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config.constants import COOKIE_TOKEN_ACESSO, MINUTOS_ENTRE_REGISTROS_ACESSO
from app.config.database import SessaoLocal
from app.utils.data_utils import agora
from app.utils.seguranca_utils import decodificar_token, e_token_de_sessao


def obter_sessao():
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()


def obter_usuario_logado(
    requisicao: Request,
    db: Session = Depends(obter_sessao),
):
    from app.models.usuario_model import Usuario

    nao_autenticado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
    )

    token = requisicao.cookies.get(COOKIE_TOKEN_ACESSO)
    if not token:
        raise nao_autenticado

    try:
        payload = decodificar_token(token)
    except JWTError as e:
        raise nao_autenticado from e

    if not e_token_de_sessao(payload):
        raise nao_autenticado

    usuario = db.query(Usuario).filter(Usuario.idusuario == int(payload["sub"])).first()
    if not usuario or not usuario.ativo:
        raise nao_autenticado

    _registrar_acesso(usuario, db)

    return usuario


def _registrar_acesso(usuario, db: Session) -> None:
    """Atualiza ultimo_acesso_em (ranking, "online", "última atividade"), no máximo
    uma vez a cada MINUTOS_ENTRE_REGISTROS_ACESSO."""
    momento = agora()
    intervalo = timedelta(minutes=MINUTOS_ENTRE_REGISTROS_ACESSO)
    if usuario.ultimo_acesso_em is None or momento - usuario.ultimo_acesso_em >= intervalo:
        usuario.ultimo_acesso_em = momento
        db.commit()


def obter_usuario_verificado(usuario=Depends(obter_usuario_logado)):
    """Como obter_usuario_logado, mas exige e-mail confirmado (RF-ID-01).

    Usado em quem escreve para outras pessoas: iniciar contato, mandar mensagem e
    propor contratação.
    """
    if usuario.email_verificado_em is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Confirme seu e-mail para enviar mensagens. Enviamos um link para {usuario.email}."
            ),
        )
    return usuario
