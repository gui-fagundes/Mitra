from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

brazil_timezone = ZoneInfo("America/Sao_Paulo")


def parse_mes_yyyymm(mes: str) -> tuple[int, int]:
    """Valida uma string 'YYYY-MM' e retorna (ano, mes). Levanta HTTPException 422 se inválido."""
    try:
        ano_str, mes_str = mes.split("-")
        if len(ano_str) != 4 or len(mes_str) != 2 or not ano_str.isdigit() or not mes_str.isdigit():
            raise ValueError
        ano, mes_num = int(ano_str), int(mes_str)
        if mes_num < 1 or mes_num > 12:
            raise ValueError
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parâmetro 'mes' deve estar no formato YYYY-MM (ex.: 2026-07)",
        ) from e
    return ano, mes_num


def get_now():
    return datetime.now()


def date_time_zone_to_string(date_time_zone: datetime):
    if date_time_zone.tzinfo is None:
        date_time_zone = date_time_zone.replace(tzinfo=brazil_timezone)

    date_time_zone = date_time_zone.astimezone(brazil_timezone)

    # pega microssegundos e converte para milissegundos
    milliseconds = date_time_zone.microsecond // 1000

    return (
        date_time_zone.strftime("%Y-%m-%dT%H:%M:%S")
        + f".{milliseconds:03d}"
        + date_time_zone.strftime("%z")
    )


def date_time_from_string(data_string: str):
    return datetime.strptime(data_string, "%Y-%m-%dT%H:%M:%S")


def date_time_from_sql_string(data_string: str):
    return datetime.strptime(data_string, "%Y-%m-%d %H:%M:%S")


def date_from_string(data_string: str):
    return datetime.strptime(data_string, "%Y-%m-%d")


def get_date_string(datetime: datetime, file_safe: bool = False, date_format: str = None):
    if not date_format:
        date_format = "%d-%m-%Y" if file_safe else "%d/%m/%Y"

    return datetime.strftime(date_format)


def get_date_sql_string(datetime: datetime):
    return datetime.strftime("%Y-%m-%d")


def get_date_time_string(datetime: datetime):
    return datetime.strftime("%d/%m/%Y %H:%M:%S")


def get_date_time_sql_string(datetime: datetime):
    return datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_date_time_iso_string(datetime: datetime):
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=brazil_timezone)

    return datetime.isoformat(timespec="seconds")
