"""CNPJ: normalização, dígitos verificadores e consulta à BrasilAPI (RF-ID-07).

Desde jul/2026 a Receita emite CNPJ alfanumérico: as 12 primeiras posições podem ter
letras (A–Z); os 2 dígitos verificadores continuam numéricos. O cálculo é o mesmo
módulo 11 de antes, usando o código ASCII − 48 de cada caractere (para dígitos,
isso dá o próprio número).
"""

import os
import re
from dataclasses import dataclass
from enum import Enum

import httpx

URL_BRASILAPI = os.getenv("BRASILAPI_URL") or "https://brasilapi.com.br/api"
SEGUNDOS_TIMEOUT = 10

_PESOS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_PESOS_2 = [6, *_PESOS_1]
_FORMATO = re.compile(r"^[0-9A-Z]{12}[0-9]{2}$")


def normalizar(cnpj: str) -> str:
    """Tira máscara e espaços e põe em maiúsculas: "12.abc.345/01de-35" → "12ABC34501DE35"."""
    return re.sub(r"[\s./-]", "", cnpj).upper()


def _digito(base: str, pesos: list[int]) -> str:
    resto = sum((ord(c) - 48) * p for c, p in zip(base, pesos, strict=True)) % 11
    return "0" if resto < 2 else str(11 - resto)


def dv_valido(cnpj: str) -> bool:
    """Formato (numérico ou alfanumérico) e dígitos verificadores. Espera CNPJ normalizado."""
    if not _FORMATO.match(cnpj) or len(set(cnpj)) == 1:
        return False
    d1 = _digito(cnpj[:12], _PESOS_1)
    d2 = _digito(cnpj[:12] + d1, _PESOS_2)
    return cnpj[12:] == d1 + d2


class SituacaoConsulta(Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"
    INEXISTENTE = "inexistente"
    INDISPONIVEL = "indisponivel"


@dataclass(frozen=True)
class ResultadoConsulta:
    situacao: SituacaoConsulta
    # Preenchidos quando a Receita conhece o CNPJ.
    descricao_situacao: str | None = None
    razao_social: str | None = None


def consultar_na_receita(cnpj: str, cliente: httpx.Client | None = None) -> ResultadoConsulta:
    """Consulta a situação cadastral na BrasilAPI. Nunca levanta: falha vira INDISPONIVEL.

    `cliente` existe para os testes injetarem um transporte falso.
    """
    try:
        if cliente is None:
            with httpx.Client(timeout=SEGUNDOS_TIMEOUT) as proprio:
                resposta = proprio.get(f"{URL_BRASILAPI}/cnpj/v1/{cnpj}")
        else:
            resposta = cliente.get(f"{URL_BRASILAPI}/cnpj/v1/{cnpj}")
    except httpx.HTTPError as e:
        print(f"BrasilAPI indisponível ao consultar CNPJ: {e!r}", flush=True)
        return ResultadoConsulta(SituacaoConsulta.INDISPONIVEL)

    if resposta.status_code == 404:
        return ResultadoConsulta(SituacaoConsulta.INEXISTENTE)
    if resposta.status_code != 200:
        print(f"BrasilAPI respondeu {resposta.status_code} ao consultar CNPJ", flush=True)
        return ResultadoConsulta(SituacaoConsulta.INDISPONIVEL)

    try:
        dados = resposta.json()
    except ValueError:
        return ResultadoConsulta(SituacaoConsulta.INDISPONIVEL)

    descricao = dados.get("descricao_situacao_cadastral")
    # situacao_cadastral 2 = ATIVA na tabela da Receita.
    ativo = dados.get("situacao_cadastral") == 2 or descricao == "ATIVA"
    return ResultadoConsulta(
        SituacaoConsulta.ATIVO if ativo else SituacaoConsulta.INATIVO,
        descricao_situacao=descricao,
        razao_social=dados.get("razao_social"),
    )
