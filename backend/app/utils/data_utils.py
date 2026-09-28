from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

fuso_brasil = ZoneInfo("America/Sao_Paulo")


def agora() -> datetime:
    """Data/hora local naive — o MVP é BR-only (ver docs/backend-plan.md)."""
    return datetime.now()


# Daqui para baixo: sem uso no MVP até agora — mantido para avaliação na limpeza
# de código morto (ver docs/backend-plan.md, "Limpeza de código sem uso").


def interpretar_mes_aaaamm(mes: str) -> tuple[int, int]:
    """Valida uma string 'AAAA-MM' e retorna (ano, mes). Levanta HTTPException 422 se inválido."""
    try:
        texto_ano, texto_mes = mes.split("-")
        if (
            len(texto_ano) != 4
            or len(texto_mes) != 2
            or not texto_ano.isdigit()
            or not texto_mes.isdigit()
        ):
            raise ValueError
        ano, numero_mes = int(texto_ano), int(texto_mes)
        if numero_mes < 1 or numero_mes > 12:
            raise ValueError
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro 'mes' deve estar no formato AAAA-MM (ex.: 2026-07)",
        ) from e
    return ano, numero_mes


def data_hora_com_fuso_para_texto(data_hora: datetime) -> str:
    if data_hora.tzinfo is None:
        data_hora = data_hora.replace(tzinfo=fuso_brasil)

    data_hora = data_hora.astimezone(fuso_brasil)

    # pega microssegundos e converte para milissegundos
    milissegundos = data_hora.microsecond // 1000

    return (
        data_hora.strftime("%Y-%m-%dT%H:%M:%S") + f".{milissegundos:03d}" + data_hora.strftime("%z")
    )


def data_hora_de_texto(texto: str) -> datetime:
    return datetime.strptime(texto, "%Y-%m-%dT%H:%M:%S")


def data_hora_de_texto_sql(texto: str) -> datetime:
    return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")


def data_de_texto(texto: str) -> datetime:
    return datetime.strptime(texto, "%Y-%m-%d")


def formatar_data(
    data_hora: datetime, seguro_para_arquivo: bool = False, formato: str | None = None
) -> str:
    if not formato:
        formato = "%d-%m-%Y" if seguro_para_arquivo else "%d/%m/%Y"

    return data_hora.strftime(formato)


def formatar_data_sql(data_hora: datetime) -> str:
    return data_hora.strftime("%Y-%m-%d")


def formatar_data_hora(data_hora: datetime) -> str:
    return data_hora.strftime("%d/%m/%Y %H:%M:%S")


def formatar_data_hora_sql(data_hora: datetime) -> str:
    return data_hora.strftime("%Y-%m-%d %H:%M:%S")


def formatar_data_hora_iso(data_hora: datetime) -> str:
    if data_hora.tzinfo is None:
        data_hora = data_hora.replace(tzinfo=fuso_brasil)

    return data_hora.isoformat(timespec="seconds")
