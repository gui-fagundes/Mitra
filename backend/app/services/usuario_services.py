from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.usuario_model import Usuario
from app.utils.seguranca_utils import gerar_hash_senha


def buscar_por_email(email: str, db: Session) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.email == email).first()


def criar_usuario(payload: dict, db: Session) -> Usuario:
    if buscar_por_email(payload["email"], db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado",
        )

    usuario = Usuario(
        nome=payload["nome"],
        email=payload["email"],
        senha_hash=gerar_hash_senha(payload["senha"]),
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario
