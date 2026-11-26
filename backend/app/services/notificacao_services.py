"""Avisos por e-mail em eventos-chave (RF-CO-03).

Toda novidade entre cliente e prestador vira uma mensagem no chat: o texto que
alguém escreveu, o primeiro contato, os eventos da contratação e os da avaliação.
Por isso os avisos saem de um único lugar: `conversa_services.adicionar_mensagem`
anota cada mensagem nova na sessão, e a rota, depois do commit, chama `agendar`,
que monta um e-mail por destinatário e o entrega ao BackgroundTasks.

Quem recebe: a outra parte da conversa, se a conta está ativa, com e-mail confirmado
e com `notificar_email` ligado.

Para não virar spam, mensagens de texto só avisam no começo de uma "rodada": não
avisa se o mesmo autor já tinha escrito há menos de MINUTOS_ENTRE_AVISOS_DE_MENSAGEM
sem resposta, nem se o destinatário escreveu na conversa há menos de
MINUTOS_DESTINATARIO_ATIVO (está conversando agora). Primeiro contato e eventos
sempre avisam.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from fastapi import BackgroundTasks
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.config.constants import EMAIL_SUPORTE, URL_FRONTEND
from app.models.conversa_model import Conversa
from app.models.mensagem_model import Mensagem
from app.models.usuario_model import Usuario
from app.utils import email_utils

CHAVE_PENDENTES = "mensagens_para_notificar"
MINUTOS_ENTRE_AVISOS_DE_MENSAGEM = 30
MINUTOS_DESTINATARIO_ATIVO = 10
TAMANHO_MAXIMO_TRECHO = 300

# Motivos, do mais para o menos importante: define o assunto quando um mesmo
# e-mail junta mais de uma novidade.
CONTATO = "contato"
AVALIACAO = "avaliacao"
CONTRATACAO = "contratacao"
MENSAGEM = "mensagem"
PRIORIDADE = (CONTATO, AVALIACAO, CONTRATACAO, MENSAGEM)


def anotar(db: Session, conversa: Conversa, mensagem: Mensagem, motivo: str) -> None:
    db.info.setdefault(CHAVE_PENDENTES, []).append((conversa, mensagem, motivo))


@dataclass
class _Aviso:
    destinatario: Usuario
    autor: Usuario
    conversa: Conversa
    motivos: set[str] = field(default_factory=set)
    linhas: list[str] = field(default_factory=list)
    idcontratacao: int | None = None


def _trecho(texto: str) -> str:
    texto = " ".join(texto.split())
    if len(texto) <= TAMANHO_MAXIMO_TRECHO:
        return texto
    return texto[: TAMANHO_MAXIMO_TRECHO - 1].rstrip() + "…"


def _pode_receber(usuario: Usuario) -> bool:
    return bool(usuario.ativo and usuario.notificar_email and usuario.email_verificado_em)


def _texto_merece_aviso(mensagem: Mensagem, destinatario: Usuario, db: Session) -> bool:
    anterior = (
        db.query(Mensagem)
        .filter(
            Mensagem.idconversa == mensagem.idconversa,
            Mensagem.idmensagem < mensagem.idmensagem,
        )
        .order_by(Mensagem.idmensagem.desc())
        .first()
    )
    if (
        anterior is not None
        and anterior.tipo == "texto"
        and anterior.idautor == mensagem.idautor
        and mensagem.criado_em - anterior.criado_em
        < timedelta(minutes=MINUTOS_ENTRE_AVISOS_DE_MENSAGEM)
    ):
        return False

    destinatario_ativo = (
        db.query(Mensagem.idmensagem)
        .filter(
            Mensagem.idconversa == mensagem.idconversa,
            Mensagem.idautor == destinatario.idusuario,
            Mensagem.tipo == "texto",
            Mensagem.criado_em
            >= mensagem.criado_em - timedelta(minutes=MINUTOS_DESTINATARIO_ATIVO),
        )
        .first()
    )
    return destinatario_ativo is None


def _assunto(aviso: _Aviso) -> str:
    motivo = next(m for m in PRIORIDADE if m in aviso.motivos)
    nome = aviso.autor.nome
    if motivo == CONTATO:
        return f"{nome} entrou em contato pelo Mitra"
    if motivo == AVALIACAO:
        return "Você recebeu uma avaliação no Mitra"
    if motivo == CONTRATACAO:
        return f"Novidade na contratação com {nome} · Mitra"
    return f"Nova mensagem de {nome} · Mitra"


def _corpo(aviso: _Aviso) -> str:
    if aviso.idcontratacao is not None and aviso.motivos & {CONTRATACAO, AVALIACAO}:
        link = f"{URL_FRONTEND}/servico/{aviso.idcontratacao}/confirmar"
    else:
        link = f"{URL_FRONTEND}/mensagens/{aviso.conversa.idconversa}"
    corpo = (
        f"Olá, {aviso.destinatario.nome}.\n\n"
        + "\n\n".join(aviso.linhas)
        + f"\n\nPara ver e responder, acesse:\n{link}\n\n"
        "—\n"
        "Você recebe estes avisos porque eles estão ligados na sua conta do Mitra. "
        "Para desligar, desmarque os avisos por e-mail em Minha conta.\n"
    )
    if EMAIL_SUPORTE:
        corpo += f"Dúvidas: {EMAIL_SUPORTE}\n"
    return corpo


def montar(pendentes: list[tuple[Conversa, Mensagem, str]], db: Session) -> list[tuple]:
    """(para, assunto, corpo) de cada e-mail a enviar, um por destinatário e conversa."""
    avisos: dict[tuple[int, int], _Aviso] = {}
    for conversa, mensagem, motivo in pendentes:
        # Mensagem desfeita por rollback (ex.: avaliação duplicada) não avisa ninguém.
        if not inspect(mensagem).persistent:
            continue
        destinatario = conversa.outra_parte(mensagem.idautor)
        if not _pode_receber(destinatario):
            continue
        if motivo == MENSAGEM and not _texto_merece_aviso(mensagem, destinatario, db):
            continue

        chave = (destinatario.idusuario, conversa.idconversa)
        aviso = avisos.get(chave)
        if aviso is None:
            autor = conversa.outra_parte(destinatario.idusuario)
            aviso = avisos[chave] = _Aviso(destinatario, autor, conversa)
        aviso.motivos.add(motivo)
        if mensagem.idcontratacao is not None:
            aviso.idcontratacao = mensagem.idcontratacao
        if mensagem.tipo == "texto":
            aviso.linhas.append(f"{aviso.autor.nome} escreveu:\n“{_trecho(mensagem.texto)}”")
        else:
            aviso.linhas.append(mensagem.texto)

    return [(a.destinatario.email, _assunto(a), _corpo(a)) for a in avisos.values()]


def agendar(tarefas: BackgroundTasks, db: Session) -> None:
    """Chamada pela rota depois do commit: envia os avisos das mensagens anotadas."""
    pendentes = db.info.pop(CHAVE_PENDENTES, [])
    for para, assunto, corpo in montar(pendentes, db):
        tarefas.add_task(email_utils.enviar_email, para, assunto, corpo)
