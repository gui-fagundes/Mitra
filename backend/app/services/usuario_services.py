from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.usuario_model import Usuario
from app.services import cidade_services
from app.utils import arquivo_utils
from app.utils.data_utils import agora
from app.utils.seguranca_utils import gerar_hash_senha


def buscar_por_email(email: str, db: Session) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.email == email).first()


def _normalizar_opcional(texto: str | None) -> str | None:
    """Espaços nas pontas saem; string vazia vira None."""
    if texto is None:
        return None
    return texto.strip() or None


def criar_usuario(payload: dict, db: Session) -> Usuario:
    if buscar_por_email(payload["email"], db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado",
        )

    if payload.get("idcidade") is not None:
        cidade_services.validar_cidade_ativa(payload["idcidade"], db)

    usuario = Usuario(
        nome=payload["nome"].strip(),
        email=payload["email"],
        senha_hash=gerar_hash_senha(payload["senha"]),
        idcidade=payload.get("idcidade"),
        telefone=_normalizar_opcional(payload.get("telefone")),
        # O schema só deixa chegar aqui com aceite_termos=true.
        aceite_termos_em=agora(),
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario


def atualizar_usuario(usuario: Usuario, payload: dict, db: Session) -> Usuario:
    """`payload` só com os campos enviados (exclude_unset)."""
    if payload.get("idcidade") is not None:
        cidade_services.validar_cidade_ativa(payload["idcidade"], db)

    if "telefone" in payload:
        payload["telefone"] = _normalizar_opcional(payload["telefone"])
    if "nome" in payload:
        payload["nome"] = payload["nome"].strip()
        if not payload["nome"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Nome não pode ficar em branco",
            )

    for campo, valor in payload.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)

    return usuario


def trocar_foto(usuario: Usuario, arquivo: UploadFile, db: Session) -> Usuario:
    foto_anterior = usuario.foto_url
    nova_foto = arquivo_utils.salvar_imagem(arquivo, "fotos")

    usuario.foto_url = nova_foto
    try:
        db.commit()
    except Exception:
        db.rollback()
        arquivo_utils.remover_arquivo(nova_foto)
        raise
    db.refresh(usuario)

    # Só apaga a antiga depois que a nova está gravada no banco.
    arquivo_utils.remover_arquivo(foto_anterior)
    return usuario


def remover_foto(usuario: Usuario, db: Session) -> Usuario:
    foto_anterior = usuario.foto_url
    usuario.foto_url = None
    db.commit()
    db.refresh(usuario)

    arquivo_utils.remover_arquivo(foto_anterior)
    return usuario
