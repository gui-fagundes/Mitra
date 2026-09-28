from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.cidade_schema import CidadeResposta
from app.schemas.taxonomia_schema import ServicoResposta

LIMITE_SERVICOS = 3

Preco = Decimal | None


def _preco(**extra):
    return Field(default=None, ge=0, max_digits=10, decimal_places=2, **extra)


class _CamposVitrine(BaseModel):
    bio: str | None = Field(default=None, max_length=400)
    preco_min: Preco = _preco()
    preco_max: Preco = _preco()
    disponibilidade: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validar_faixa(self):
        if (
            self.preco_min is not None
            and self.preco_max is not None
            and self.preco_min > self.preco_max
        ):
            raise ValueError("O preço mínimo não pode ser maior que o máximo")
        return self


def _validar_servicos(ids: list[int] | None) -> list[int] | None:
    if ids is None:
        return ids
    if len(ids) != len(set(ids)):
        raise ValueError("Serviço repetido na lista")
    if len(ids) > LIMITE_SERVICOS:
        raise ValueError(f"Escolha no máximo {LIMITE_SERVICOS} serviços")
    return ids


class VitrineCriacao(_CamposVitrine):
    servicos: list[int] = Field(default_factory=list)

    _servicos = field_validator("servicos")(_validar_servicos)


class VitrineAtualizacao(_CamposVitrine):
    """Campos ausentes não mudam; `servicos`, quando enviado, substitui a lista toda."""

    servicos: list[int] | None = None

    _servicos = field_validator("servicos")(_validar_servicos)


class CnpjEntrada(BaseModel):
    """Aceita com ou sem máscara (12.345.678/0001-95 ou 12345678000195)."""

    cnpj: str = Field(min_length=14, max_length=18)


class ItemPortfolioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idprestadorportfolio: int
    imagem_url: str
    legenda: str | None
    ordem: int


class LegendaPortfolioAtualizacao(BaseModel):
    legenda: str | None = Field(default=None, max_length=255)


class OrdemPortfolioEntrada(BaseModel):
    """Todos os ids do portfólio, na nova ordem."""

    ids: list[int]


class CategoriaResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idcategoria: int
    nome: str
    slug: str


class VitrineResposta(BaseModel):
    """O que o próprio prestador vê da vitrine."""

    model_config = ConfigDict(from_attributes=True)

    idprestadorperfil: int
    bio: str | None
    preco_min: float | None
    preco_max: float | None
    disponibilidade: str | None
    servicos: list[ServicoResposta] = Field(validation_alias="servicos_ordenados")
    portfolio: list[ItemPortfolioResposta]
    # Só o próprio prestador vê o número; o público vê apenas o selo.
    cnpj: str | None
    cnpj_validado: bool
    cnpj_validado_em: datetime | None
    criado_em: datetime
    atualizado_em: datetime


class PrestadorPublicoResposta(BaseModel):
    """Perfil público (RF-BS-02). Montado no service a partir de usuario + vitrine."""

    idusuario: int
    nome: str
    foto_url: str | None
    cidade: CidadeResposta | None
    bio: str | None
    preco_min: float | None
    preco_max: float | None
    disponibilidade: str | None
    cnpj_validado: bool
    prestador_desde: datetime
    ultimo_acesso_em: datetime | None
    categorias: list[CategoriaResumo]
    servicos: list[ServicoResposta]
    portfolio: list[ItemPortfolioResposta]
    servicos_concluidos: int
    # Preenchidos pela etapa de avaliações.
    nota_media: float | None = None
    qtd_avaliacoes: int = 0


class CartaoPrestadorResposta(BaseModel):
    """Card de um prestador no resultado da busca."""

    idusuario: int
    nome: str
    foto_url: str | None
    cidade: CidadeResposta | None
    bio: str | None
    preco_min: float | None
    preco_max: float | None
    cnpj_validado: bool
    servicos: list[ServicoResposta]
    ultimo_acesso_em: datetime | None
    nota_media: float | None
    qtd_avaliacoes: int


class ResultadoBuscaResposta(BaseModel):
    total: int
    itens: list[CartaoPrestadorResposta]
