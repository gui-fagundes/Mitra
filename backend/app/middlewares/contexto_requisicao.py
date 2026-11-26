"""Identificador e IP de cada requisição, disponíveis para quem registra auditoria e
erros (RF-AD-02, RNF-DI-02) sem precisar mudar a assinatura dos services.

O middleware cria um ContextoRequisicao e o guarda numa ContextVar. O objeto é
compartilhado (não copiado) com as camadas internas, então quando
obter_usuario_logado preenche `idusuario`, o registro de erro do middleware de
fora também enxerga quem estava logado.
"""

import re
import uuid
from contextvars import ContextVar
from dataclasses import dataclass

from fastapi import Request

from app.config.constants import CONFIAR_X_FORWARDED_FOR

CABECALHO_ID = "X-Request-ID"
# Aceita o id vindo do cliente/proxy só se for curto e sem caracteres estranhos.
_ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


@dataclass
class ContextoRequisicao:
    idrequisicao: str | None = None
    ip: str | None = None
    idusuario: int | None = None


_contexto: ContextVar[ContextoRequisicao | None] = ContextVar("contexto_requisicao", default=None)


def contexto_atual() -> ContextoRequisicao:
    """O contexto da requisição em andamento; fora de uma requisição, um vazio."""
    return _contexto.get() or ContextoRequisicao()


def _ip_do_cliente(requisicao: Request) -> str | None:
    # Só confia no X-Forwarded-For atrás de um proxy conhecido: sem proxy,
    # qualquer cliente poderia escolher o IP que aparece na auditoria.
    if CONFIAR_X_FORWARDED_FOR:
        encaminhado = requisicao.headers.get("x-forwarded-for")
        if encaminhado:
            return encaminhado.split(",")[0].strip()[:45] or None
    return requisicao.client.host if requisicao.client else None


async def registrar_contexto(requisicao: Request, proximo):
    recebido = requisicao.headers.get(CABECALHO_ID)
    idrequisicao = recebido if recebido and _ID_VALIDO.match(recebido) else uuid.uuid4().hex
    marca = _contexto.set(
        ContextoRequisicao(idrequisicao=idrequisicao, ip=_ip_do_cliente(requisicao))
    )
    try:
        resposta = await proximo(requisicao)
    finally:
        _contexto.reset(marca)
    resposta.headers[CABECALHO_ID] = idrequisicao
    return resposta
