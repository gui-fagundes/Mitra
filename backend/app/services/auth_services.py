from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.constants import TOKEN_EXPIRATION_TIME
from app.models.usuario_model import Usuario
from app.services import usuario_services
from app.utils.auth_utils import criar_token, verificar_senha
from app.utils.datetime_utils import get_now


def gerar_token(usuario: Usuario) -> str:
    expira_em = get_now() + timedelta(minutes=TOKEN_EXPIRATION_TIME)
    return criar_token({"sub": str(usuario.idusuario), "exp": int(expira_em.timestamp())})


def login(payload: dict, db: Session) -> Usuario:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha inválidos",
    )

    usuario = usuario_services.buscar_por_email(payload["email"], db)
    if not usuario or not verificar_senha(payload["senha"], usuario.senha_hash):
        raise unauthorized

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    return usuario


def signup(payload: dict, db: Session) -> Usuario:
    return usuario_services.criar_usuario(payload, db)
