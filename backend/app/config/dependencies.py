from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config.constants import COOKIE_TOKEN_ACESSO
from app.config.database import SessaoLocal
from app.utils.seguranca_utils import decodificar_token


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

    if not payload:
        raise nao_autenticado

    idusuario = payload.get("sub")
    if idusuario is None:
        raise nao_autenticado

    usuario = db.query(Usuario).filter(Usuario.idusuario == int(idusuario)).first()
    if not usuario or not usuario.ativo:
        raise nao_autenticado

    return usuario
