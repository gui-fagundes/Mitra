from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao, obter_usuario_logado
from app.models.usuario_model import Usuario
from app.schemas.prestador_schema import (
    PrestadorPublicoResposta,
    VitrineAtualizacao,
    VitrineCriacao,
    VitrineResposta,
)
from app.services import prestador_services

# A vitrine do próprio usuário mora sob /conta, como os demais recursos do logado.
rotas_vitrine = APIRouter(prefix="/conta/vitrine", tags=["Vitrine do prestador"])
rotas_prestador = APIRouter(prefix="/prestadores", tags=["Prestadores"])


@rotas_vitrine.post("", response_model=VitrineResposta, status_code=201)
def criar_vitrine(
    corpo: VitrineCriacao,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return prestador_services.criar_vitrine(usuario_logado, corpo.model_dump(), db)


@rotas_vitrine.get("", response_model=VitrineResposta)
def obter_vitrine(usuario_logado: Usuario = Depends(obter_usuario_logado)):
    return prestador_services.obter_vitrine(usuario_logado)


@rotas_vitrine.patch("", response_model=VitrineResposta)
def atualizar_vitrine(
    corpo: VitrineAtualizacao,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return prestador_services.atualizar_vitrine(
        usuario_logado, corpo.model_dump(exclude_unset=True), db
    )


@rotas_prestador.get("/{idusuario}", response_model=PrestadorPublicoResposta)
def obter_prestador(idusuario: int, db: Session = Depends(obter_sessao)):
    """Perfil público (RF-BS-02). Não exige login."""
    return prestador_services.obter_prestador_publico(idusuario, db)
