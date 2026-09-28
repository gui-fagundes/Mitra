from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.constants import MINUTOS_EXPIRACAO_TOKEN
from app.models.usuario_model import Usuario
from app.services import usuario_services
from app.utils.data_utils import agora
from app.utils.seguranca_utils import criar_token, verificar_senha


def gerar_token(usuario: Usuario) -> str:
    expira_em = agora() + timedelta(minutes=MINUTOS_EXPIRACAO_TOKEN)
    return criar_token({"sub": str(usuario.idusuario), "exp": int(expira_em.timestamp())})


def entrar(payload: dict, db: Session) -> Usuario:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha inválidos",
    )

    usuario = usuario_services.buscar_por_email(payload["email"], db)
    if not usuario or not verificar_senha(payload["senha"], usuario.senha_hash):
        raise credenciais_invalidas

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    return usuario


def cadastrar(payload: dict, db: Session) -> Usuario:
    return usuario_services.criar_usuario(payload, db)


def atualizar(usuario: Usuario, payload: dict, db: Session) -> Usuario:
    return usuario_services.atualizar_usuario(usuario, payload, db)
