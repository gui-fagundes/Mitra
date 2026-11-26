"""Avaliações (RF-RE-01 a 03): o cliente avalia o prestador depois da conclusão
bilateral; o prestador pode responder uma vez. Nada disso é editável."""

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.avaliacao_model import Avaliacao
from app.models.contratacao_model import Contratacao
from app.models.conversa_model import Conversa
from app.models.usuario_model import Usuario
from app.services import conversa_services, notificacao_services
from app.utils.data_utils import agora

DIAS_PARA_AVALIAR = 30


def _texto_opcional(texto: str | None) -> str | None:
    if texto is None:
        return None
    return texto.strip() or None


def nome_abreviado(nome: str) -> str:
    """ "Cristina Souza Lima" → "Cristina L."; nome único fica como está."""
    partes = nome.split()
    if len(partes) < 2:
        return nome
    return f"{partes[0]} {partes[-1][0].upper()}."


# --- Prazo e permissões -------------------------------------------------------------


def avaliar_ate(contratacao: Contratacao):
    if contratacao.concluido_em is None:
        return None
    return contratacao.concluido_em + timedelta(days=DIAS_PARA_AVALIAR)


def pode_avaliar(contratacao: Contratacao, idusuario: int) -> bool:
    """Cliente, contratação concluída, ainda não avaliada e dentro do prazo."""
    prazo = avaliar_ate(contratacao)
    return (
        contratacao.estado == "concluido"
        and contratacao.papel_de(idusuario) == "cliente"
        and contratacao.avaliacao is None
        and prazo is not None
        and agora() <= prazo
    )


def pode_responder(contratacao: Contratacao, idusuario: int) -> bool:
    return (
        contratacao.papel_de(idusuario) == "prestador"
        and contratacao.avaliacao is not None
        and contratacao.avaliacao.resposta is None
    )


# --- Estatísticas (perfil, busca e ranking usam as mesmas) ---------------------------


def _do_prestador(agregado, coluna_idusuario):
    """Subconsulta escalar sobre as avaliações cujo prestador é `coluna_idusuario`.

    Usada direto (sem embrulhar em .subquery()) para que, recebendo uma coluna da
    consulta de fora (ex.: PrestadorPerfil.idusuario), ela seja correlacionada linha
    a linha. Dentro de uma tabela derivada o SQLAlchemy não correlaciona, e a média
    sairia calculada sobre todos os prestadores.
    """
    return (
        select(agregado)
        .select_from(Avaliacao)
        .join(Contratacao, Contratacao.idcontratacao == Avaliacao.idcontratacao)
        .join(Conversa, Conversa.idconversa == Contratacao.idconversa)
        .where(Conversa.idprestador == coluna_idusuario)
        .scalar_subquery()
    )


def subconsulta_nota_media(coluna_idusuario):
    return _do_prestador(func.avg(Avaliacao.nota), coluna_idusuario)


def subconsulta_qtd_avaliacoes(coluna_idusuario):
    return _do_prestador(func.count(Avaliacao.idavaliacao), coluna_idusuario)


def estatisticas(idusuario: int, db: Session) -> tuple[float | None, int]:
    """(nota média, quantidade) de avaliações do prestador."""
    media, qtd = db.execute(
        select(subconsulta_nota_media(idusuario), subconsulta_qtd_avaliacoes(idusuario))
    ).one()
    return (round(float(media), 2) if media is not None else None), qtd


def destaques(idsusuario: list[int], db: Session) -> dict[int, str]:
    """Trecho do comentário mais recente de cada prestador (card da busca)."""
    if not idsusuario:
        return {}
    linhas = db.execute(
        select(Conversa.idprestador, Avaliacao.comentario)
        .join(Contratacao, Contratacao.idconversa == Conversa.idconversa)
        .join(Avaliacao, Avaliacao.idcontratacao == Contratacao.idcontratacao)
        .where(Conversa.idprestador.in_(idsusuario), Avaliacao.comentario.is_not(None))
        .order_by(Avaliacao.criado_em.desc())
    ).all()
    resultado: dict[int, str] = {}
    for idprestador, comentario in linhas:
        resultado.setdefault(idprestador, comentario)
    return resultado


# --- Ações --------------------------------------------------------------------------


def _publica(avaliacao: Avaliacao) -> dict:
    contratacao = avaliacao.contratacao
    return {
        "idavaliacao": avaliacao.idavaliacao,
        "idcontratacao": avaliacao.idcontratacao,
        "nota": avaliacao.nota,
        "comentario": avaliacao.comentario,
        "autor": nome_abreviado(contratacao.conversa.cliente.nome),
        "servico": contratacao.servico.nome,
        "criado_em": avaliacao.criado_em,
        "resposta": avaliacao.resposta,
        "resposta_em": avaliacao.resposta_em,
    }


def avaliar(usuario: Usuario, idcontratacao: int, payload: dict, db: Session) -> dict:
    # Import local: contratacao_services importa este módulo (resumo da contratação).
    from app.services.contratacao_services import obter_participando

    contratacao = obter_participando(usuario, idcontratacao, db)
    if contratacao.papel_de(usuario.idusuario) != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só o cliente avalia o serviço",
        )
    if contratacao.estado != "concluido":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A avaliação é liberada quando os dois confirmam a conclusão",
        )
    if contratacao.avaliacao is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este serviço já foi avaliado",
        )
    if agora() > avaliar_ate(contratacao):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"O prazo para avaliar ({DIAS_PARA_AVALIAR} dias após a conclusão) terminou",
        )

    avaliacao = Avaliacao(
        contratacao=contratacao,
        nota=payload["nota"],
        comentario=_texto_opcional(payload.get("comentario")),
    )
    db.add(avaliacao)
    conversa_services.adicionar_mensagem(
        contratacao.conversa,
        usuario.idusuario,
        f"{usuario.nome} avaliou o serviço ({payload['nota']}★)",
        db,
        tipo="evento",
        idcontratacao=contratacao.idcontratacao,
        motivo=notificacao_services.AVALIACAO,
    )
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este serviço já foi avaliado",
        ) from e
    db.refresh(avaliacao)
    return _publica(avaliacao)


def responder(usuario: Usuario, idavaliacao: int, payload: dict, db: Session) -> dict:
    avaliacao = db.get(Avaliacao, idavaliacao)
    if avaliacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avaliação não encontrada",
        )
    contratacao = avaliacao.contratacao
    if contratacao.conversa.idprestador != usuario.idusuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só o prestador avaliado pode responder",
        )
    if avaliacao.resposta is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta avaliação já foi respondida",
        )
    texto = payload["texto"].strip()
    if not texto:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A resposta está vazia",
        )

    avaliacao.resposta = texto
    avaliacao.resposta_em = agora()
    conversa_services.adicionar_mensagem(
        contratacao.conversa,
        usuario.idusuario,
        f"{usuario.nome} respondeu à avaliação",
        db,
        tipo="evento",
        idcontratacao=contratacao.idcontratacao,
    )
    db.commit()
    db.refresh(avaliacao)
    return _publica(avaliacao)


def listar_do_prestador(idusuario: int, db: Session, limite: int = 20, deslocamento: int = 0):
    """Lista pública, da mais recente para a mais antiga. 404 se não é prestador ativo."""
    prestador = db.get(Usuario, idusuario)
    if not prestador or not prestador.ativo or prestador.prestador_perfil is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prestador não encontrado",
        )

    consulta = (
        db.query(Avaliacao)
        .join(Contratacao, Contratacao.idcontratacao == Avaliacao.idcontratacao)
        .join(Conversa, Conversa.idconversa == Contratacao.idconversa)
        .filter(Conversa.idprestador == idusuario)
    )
    total = consulta.count()
    itens = (
        consulta.order_by(Avaliacao.criado_em.desc(), Avaliacao.idavaliacao.desc())
        .offset(deslocamento)
        .limit(limite)
        .all()
    )
    media, _ = estatisticas(idusuario, db)
    return {"total": total, "nota_media": media, "itens": [_publica(a) for a in itens]}
