from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TAMANHO_MAXIMO_MENSAGEM = 2000


class ConversaCriacao(BaseModel):
    """Iniciar contato com um prestador: a conversa nasce com a primeira mensagem."""

    idprestador: int
    texto: str = Field(min_length=1, max_length=TAMANHO_MAXIMO_MENSAGEM)


class MensagemEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=TAMANHO_MAXIMO_MENSAGEM)


class ParticipanteResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idusuario: int
    nome: str
    foto_url: str | None
    # Para o indicador "online" (acesso nos últimos minutos).
    ultimo_acesso_em: datetime | None


class MensagemResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idmensagem: int
    idconversa: int
    idautor: int
    tipo: Literal["texto", "evento"]
    texto: str
    criado_em: datetime


class ConversaResposta(BaseModel):
    """Uma conversa vista por um dos participantes."""

    idconversa: int
    # Papel de quem está vendo: "cliente" iniciou o contato; "prestador" é o procurado.
    papel: Literal["cliente", "prestador"]
    outra_parte: ParticipanteResposta
    ultima_mensagem: MensagemResposta | None
    criado_em: datetime
    atualizado_em: datetime


class PaginaMensagensResposta(BaseModel):
    """Mensagens em ordem cronológica (mais antiga primeiro)."""

    itens: list[MensagemResposta]
    tem_mais_antigas: bool
