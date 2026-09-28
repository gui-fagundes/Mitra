from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.prestador_perfil_model import PrestadorPerfil
from app.models.prestador_portfolio_model import PrestadorPortfolio
from app.models.usuario_model import Usuario
from app.services.prestador_services import obter_vitrine
from app.utils import arquivo_utils

LIMITE_PORTFOLIO = 10


def _legenda(texto: str | None) -> str | None:
    if texto is None:
        return None
    return texto.strip() or None


def _obter_item(perfil: PrestadorPerfil, idprestadorportfolio: int) -> PrestadorPortfolio:
    """Só itens do próprio portfólio; o de outro prestador é tratado como inexistente."""
    for item in perfil.portfolio:
        if item.idprestadorportfolio == idprestadorportfolio:
            return item
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Imagem do portfólio não encontrada",
    )


def _renumerar(perfil: PrestadorPerfil) -> None:
    for posicao, item in enumerate(sorted(perfil.portfolio, key=lambda i: i.ordem)):
        item.ordem = posicao


def adicionar(
    usuario: Usuario, arquivo: UploadFile, legenda: str | None, db: Session
) -> PrestadorPortfolio:
    perfil = obter_vitrine(usuario)
    # Checa o limite antes de gravar qualquer coisa em disco.
    if len(perfil.portfolio) >= LIMITE_PORTFOLIO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"O portfólio já tem o máximo de {LIMITE_PORTFOLIO} imagens",
        )

    imagem_url = arquivo_utils.salvar_imagem(arquivo, "portfolio")
    item = PrestadorPortfolio(
        imagem_url=imagem_url,
        legenda=_legenda(legenda),
        ordem=len(perfil.portfolio),
    )
    perfil.portfolio.append(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        arquivo_utils.remover_arquivo(imagem_url)
        raise
    db.refresh(item)
    return item


def editar_legenda(
    usuario: Usuario, idprestadorportfolio: int, payload: dict, db: Session
) -> PrestadorPortfolio:
    item = _obter_item(obter_vitrine(usuario), idprestadorportfolio)
    item.legenda = _legenda(payload.get("legenda"))
    db.commit()
    db.refresh(item)
    return item


def remover(usuario: Usuario, idprestadorportfolio: int, db: Session) -> None:
    perfil = obter_vitrine(usuario)
    item = _obter_item(perfil, idprestadorportfolio)
    imagem_url = item.imagem_url

    perfil.portfolio.remove(item)  # delete-orphan apaga a linha
    _renumerar(perfil)
    db.commit()

    # Só apaga o arquivo depois que a linha saiu do banco.
    arquivo_utils.remover_arquivo(imagem_url)


def reordenar(usuario: Usuario, ids: list[int], db: Session) -> list[PrestadorPortfolio]:
    """`ids` precisa ter exatamente as imagens do portfólio, na nova ordem."""
    perfil = obter_vitrine(usuario)
    por_id = {item.idprestadorportfolio: item for item in perfil.portfolio}
    if len(ids) != len(por_id) or set(ids) != set(por_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A nova ordem precisa conter todas as imagens do portfólio, uma vez cada",
        )

    for posicao, idprestadorportfolio in enumerate(ids):
        por_id[idprestadorportfolio].ordem = posicao
    db.commit()

    return sorted(perfil.portfolio, key=lambda i: i.ordem)
