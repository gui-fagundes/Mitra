from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config.constants import ACCESS_TOKEN_COOKIE
from app.config.database import SessionLocal
from app.utils.auth_utils import decrypt_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    from app.models.usuario_model import Usuario

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
    )

    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise unauthorized

    try:
        payload = decrypt_token(token)
    except JWTError as e:
        raise unauthorized from e

    if not payload:
        raise unauthorized

    id_usuario = payload.get("sub")
    if id_usuario is None:
        raise unauthorized

    usuario = db.query(Usuario).filter(Usuario.idusuario == int(id_usuario)).first()
    if not usuario or not usuario.ativo:
        raise unauthorized

    return usuario
