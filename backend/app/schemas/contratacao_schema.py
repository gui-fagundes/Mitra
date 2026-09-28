from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.conversa_schema import ParticipanteResposta
from app.schemas.taxonomia_schema import ServicoResposta

Estado = Literal["proposta", "combinado", "concluido", "cancelado"]


def _valor(**extra):
    return Field(default=None, ge=0, max_digits=10, decimal_places=2, **extra)


class PropostaEntrada(BaseModel):
    """Proposta de prestação de serviço feita dentro de uma conversa."""

    idservico: int
    descricao: str = Field(min_length=1, max_length=2000)
    local: str | None = Field(default=None, max_length=255)
    data_prevista: date | None = None
    # Orçamento do prestador ou budget do cliente.
    valor_estimado: Decimal | None = _valor()


class PropostaAtualizacao(BaseModel):
    """Campos ausentes não mudam. Quem edita já aceita a nova versão; o aceite do outro cai."""

    idservico: int | None = None
    descricao: str | None = Field(default=None, min_length=1, max_length=2000)
    local: str | None = Field(default=None, max_length=255)
    data_prevista: date | None = None
    valor_estimado: Decimal | None = _valor()

    @model_validator(mode="after")
    def proibir_nulo_nos_obrigatorios(self):
        for campo in ("idservico", "descricao"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"'{campo}' não pode ser nulo")
        return self


class ConclusaoEntrada(BaseModel):
    """Confirma que o serviço foi feito. `valor_final` é o preço cobrado; obrigatório se
    ninguém informou ainda. Mudar o valor derruba a confirmação do outro lado."""

    valor_final: Decimal | None = _valor()


class CancelamentoEntrada(BaseModel):
    motivo: str | None = Field(default=None, max_length=255)


class ContratacaoResposta(BaseModel):
    """Uma contratação vista por um dos participantes."""

    idcontratacao: int
    idconversa: int
    papel: Literal["cliente", "prestador"]
    outra_parte: ParticipanteResposta
    idproponente: int
    servico: ServicoResposta
    descricao: str
    local: str | None
    data_prevista: date | None
    valor_estimado: float | None
    estado: Estado
    aceite_cliente_em: datetime | None
    aceite_prestador_em: datetime | None
    combinado_em: datetime | None
    valor_final: float | None
    conclusao_cliente_em: datetime | None
    conclusao_prestador_em: datetime | None
    concluido_em: datetime | None
    cancelado_em: datetime | None
    idcancelado_por: int | None
    motivo_cancelamento: str | None
    # Há algo para quem está vendo fazer (aceitar a proposta / confirmar a conclusão).
    aguardando_voce: bool
    criado_em: datetime
    atualizado_em: datetime
