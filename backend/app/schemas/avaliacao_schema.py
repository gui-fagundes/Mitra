from datetime import datetime

from pydantic import BaseModel, Field

TAMANHO_MAXIMO_TEXTO = 1000


class AvaliacaoEntrada(BaseModel):
    nota: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=TAMANHO_MAXIMO_TEXTO)


class RespostaEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=TAMANHO_MAXIMO_TEXTO)


class AvaliacaoResposta(BaseModel):
    """Avaliação como aparece publicamente."""

    idavaliacao: int
    idcontratacao: int
    nota: int
    comentario: str | None
    # Nome abreviado do cliente ("Cris S."): o comentário é público, o nome inteiro não precisa ser.
    autor: str
    servico: str
    criado_em: datetime
    resposta: str | None
    resposta_em: datetime | None


class PaginaAvaliacoesResposta(BaseModel):
    total: int
    nota_media: float | None
    itens: list[AvaliacaoResposta]
