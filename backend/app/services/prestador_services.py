from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.prestador_perfil_model import PrestadorPerfil
from app.models.servico_model import Servico
from app.models.usuario_model import Usuario

CAMPOS_VITRINE = ("bio", "preco_min", "preco_max", "disponibilidade")


def _texto_opcional(texto: str | None) -> str | None:
    if texto is None:
        return None
    return texto.strip() or None


def _carregar_servicos(ids: list[int], db: Session) -> list[Servico]:
    """Serviços ativos com esses ids; 422 se algum não existir ou estiver inativo."""
    if not ids:
        return []
    servicos = db.query(Servico).filter(Servico.idservico.in_(ids), Servico.ativo.is_(True)).all()
    if len(servicos) != len(set(ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Serviço inválido",
        )
    return servicos


def _aplicar_campos(perfil: PrestadorPerfil, payload: dict) -> None:
    for campo in CAMPOS_VITRINE:
        if campo in payload:
            valor = payload[campo]
            if campo in ("bio", "disponibilidade"):
                valor = _texto_opcional(valor)
            setattr(perfil, campo, valor)

    # O schema valida a faixa quando os dois vêm juntos; aqui cobre a mistura
    # do que veio no PATCH com o que já estava salvo.
    if (
        perfil.preco_min is not None
        and perfil.preco_max is not None
        and perfil.preco_min > perfil.preco_max
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="O preço mínimo não pode ser maior que o máximo",
        )


def obter_vitrine(usuario: Usuario) -> PrestadorPerfil:
    if usuario.prestador_perfil is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você ainda não tem vitrine de prestador",
        )
    return usuario.prestador_perfil


def criar_vitrine(usuario: Usuario, payload: dict, db: Session) -> PrestadorPerfil:
    """Transforma um usuário que só contrata em prestador (RF-ID-03)."""
    if usuario.prestador_perfil is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já tem uma vitrine de prestador",
        )

    perfil = PrestadorPerfil()
    _aplicar_campos(perfil, payload)
    perfil.servicos = _carregar_servicos(payload.get("servicos", []), db)
    usuario.prestador_perfil = perfil

    db.commit()
    db.refresh(perfil)
    return perfil


def atualizar_vitrine(usuario: Usuario, payload: dict, db: Session) -> PrestadorPerfil:
    """`payload` só com os campos enviados (exclude_unset)."""
    perfil = obter_vitrine(usuario)

    _aplicar_campos(perfil, payload)
    if payload.get("servicos") is not None:
        perfil.servicos = _carregar_servicos(payload["servicos"], db)

    db.commit()
    db.refresh(perfil)
    return perfil


def obter_prestador_publico(idusuario: int, db: Session) -> dict:
    """Dados do perfil público. 404 se não é prestador ou a conta está inativa."""
    usuario = db.get(Usuario, idusuario)
    if not usuario or not usuario.ativo or usuario.prestador_perfil is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prestador não encontrado",
        )

    perfil = usuario.prestador_perfil
    return {
        "idusuario": usuario.idusuario,
        "nome": usuario.nome,
        "foto_url": usuario.foto_url,
        "cidade": usuario.cidade,
        "bio": perfil.bio,
        "preco_min": perfil.preco_min,
        "preco_max": perfil.preco_max,
        "disponibilidade": perfil.disponibilidade,
        "cnpj_validado": perfil.cnpj_validado,
        "prestador_desde": perfil.criado_em,
        "ultimo_acesso_em": usuario.ultimo_acesso_em,
        "categorias": perfil.categorias,
        "servicos": perfil.servicos_ordenados,
    }
