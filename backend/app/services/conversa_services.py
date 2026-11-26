"""Chat entre cliente e prestador (RF-CO-02). Independente da contratação."""

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.conversa_model import Conversa
from app.models.mensagem_model import Mensagem
from app.models.usuario_model import Usuario
from app.services import notificacao_services
from app.utils.data_utils import agora


def _texto(payload: dict) -> str:
    texto = payload["texto"].strip()
    if not texto:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A mensagem está vazia",
        )
    return texto


def obter_participando(idconversa: int, usuario: Usuario, db: Session) -> Conversa:
    """A conversa, se o usuário participa dela. 404 se não existe, 403 se é de outros."""
    conversa = db.get(Conversa, idconversa)
    if conversa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa não encontrada",
        )
    if not conversa.participa(usuario.idusuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não participa desta conversa",
        )
    return conversa


def adicionar_mensagem(
    conversa: Conversa,
    idautor: int,
    texto: str,
    db: Session,
    tipo: str = "texto",
    idcontratacao: int | None = None,
    motivo: str | None = None,
) -> Mensagem:
    """Acrescenta a mensagem e move a conversa para o topo. Não faz commit.

    A mensagem fica anotada para o aviso por e-mail à outra parte; `motivo` muda o
    assunto do aviso (padrão: mensagem para texto, contratação para evento).
    """
    mensagem = Mensagem(
        idconversa=conversa.idconversa,
        idautor=idautor,
        tipo=tipo,
        texto=texto,
        idcontratacao=idcontratacao,
    )
    db.add(mensagem)
    conversa.atualizado_em = agora()
    if motivo is None:
        motivo = (
            notificacao_services.MENSAGEM if tipo == "texto" else notificacao_services.CONTRATACAO
        )
    notificacao_services.anotar(db, conversa, mensagem, motivo)
    return mensagem


def resumo(conversa: Conversa, usuario: Usuario, ultima: Mensagem | None) -> dict:
    """A conversa do ponto de vista de quem está vendo."""
    return {
        "idconversa": conversa.idconversa,
        "papel": "cliente" if usuario.idusuario == conversa.idcliente else "prestador",
        "outra_parte": conversa.outra_parte(usuario.idusuario),
        "ultima_mensagem": ultima,
        "criado_em": conversa.criado_em,
        "atualizado_em": conversa.atualizado_em,
    }


def _ultima_mensagem(idconversa: int, db: Session) -> Mensagem | None:
    return (
        db.query(Mensagem)
        .filter(Mensagem.idconversa == idconversa)
        .order_by(Mensagem.idmensagem.desc())
        .first()
    )


def iniciar(usuario: Usuario, payload: dict, db: Session) -> tuple[dict, bool]:
    """Abre (ou reaproveita) a conversa com o prestador e envia a primeira mensagem.

    Devolve (conversa, criou_agora).
    """
    texto = _texto(payload)
    idprestador = payload["idprestador"]

    if idprestador == usuario.idusuario:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Você não pode iniciar uma conversa com você mesmo",
        )
    prestador = db.get(Usuario, idprestador)
    if not prestador or not prestador.ativo or prestador.prestador_perfil is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prestador não encontrado",
        )

    conversa = (
        db.query(Conversa)
        .filter(Conversa.idcliente == usuario.idusuario, Conversa.idprestador == idprestador)
        .first()
    )
    criou = conversa is None
    if criou:
        conversa = Conversa(idcliente=usuario.idusuario, idprestador=idprestador)
        db.add(conversa)
        db.flush()  # precisa do idconversa para a mensagem

    mensagem = adicionar_mensagem(
        conversa,
        usuario.idusuario,
        texto,
        db,
        motivo=notificacao_services.CONTATO if criou else None,
    )
    db.commit()
    db.refresh(conversa)
    db.refresh(mensagem)
    return resumo(conversa, usuario, mensagem), criou


def listar(usuario: Usuario, db: Session) -> list[dict]:
    """Conversas do usuário (como cliente ou prestador), da mais recente à mais antiga."""
    conversas = (
        db.query(Conversa)
        .filter(
            or_(Conversa.idcliente == usuario.idusuario, Conversa.idprestador == usuario.idusuario)
        )
        .order_by(Conversa.atualizado_em.desc(), Conversa.idconversa.desc())
        .all()
    )
    if not conversas:
        return []

    # Última mensagem de cada conversa numa consulta só.
    ids_ultimas = (
        db.query(func.max(Mensagem.idmensagem))
        .filter(Mensagem.idconversa.in_([c.idconversa for c in conversas]))
        .group_by(Mensagem.idconversa)
    )
    ultimas = {
        m.idconversa: m
        for m in db.query(Mensagem).filter(Mensagem.idmensagem.in_(ids_ultimas.scalar_subquery()))
    }
    return [resumo(c, usuario, ultimas.get(c.idconversa)) for c in conversas]


def obter(usuario: Usuario, idconversa: int, db: Session) -> dict:
    conversa = obter_participando(idconversa, usuario, db)
    return resumo(conversa, usuario, _ultima_mensagem(idconversa, db))


def listar_mensagens(
    usuario: Usuario,
    idconversa: int,
    db: Session,
    antes_de: int | None = None,
    depois_de: int | None = None,
    limite: int = 50,
) -> dict:
    """Histórico em ordem cronológica.

    - sem cursores: as `limite` mais recentes;
    - `antes_de`: página anterior (rolar para cima);
    - `depois_de`: só as novas desde a última vista (polling).
    """
    obter_participando(idconversa, usuario, db)
    consulta = db.query(Mensagem).filter(Mensagem.idconversa == idconversa)

    if depois_de is not None:
        novas = (
            consulta.filter(Mensagem.idmensagem > depois_de)
            .order_by(Mensagem.idmensagem)
            .limit(limite)
            .all()
        )
        return {"itens": novas, "tem_mais_antigas": False}

    if antes_de is not None:
        consulta = consulta.filter(Mensagem.idmensagem < antes_de)
    pagina = consulta.order_by(Mensagem.idmensagem.desc()).limit(limite + 1).all()
    tem_mais = len(pagina) > limite
    return {"itens": list(reversed(pagina[:limite])), "tem_mais_antigas": tem_mais}


def enviar(usuario: Usuario, idconversa: int, payload: dict, db: Session) -> Mensagem:
    conversa = obter_participando(idconversa, usuario, db)
    mensagem = adicionar_mensagem(conversa, usuario.idusuario, _texto(payload), db)
    db.commit()
    db.refresh(mensagem)
    return mensagem
