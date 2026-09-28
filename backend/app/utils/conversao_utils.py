# Sem uso no MVP até agora — mantido para avaliação na limpeza de código morto
# (ver docs/backend-plan.md, "Limpeza de código sem uso").
import base64
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID


def base64_para_bytes(texto: str) -> bytes:
    return base64.b64decode(texto)


def bytes_para_base64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("utf-8")


def base64_para_texto(dados_base64: str) -> str:
    dados = base64.b64decode(dados_base64)

    return dados.decode("utf-8")


def dict_para_texto(obj):
    texto_json = json.dumps(obj, default=__serializar, ensure_ascii=False)
    return texto_json.encode("utf-8").decode("utf-8")


def texto_para_dict(texto: str, ocultar_subcorpos: bool = False):
    dados = json.loads(texto)

    if ocultar_subcorpos:
        dados = __ocultar_subcorpos(dados)

    return dados


def xml_para_dict(texto_xml: str, ignorar_namespaces: bool = False) -> dict:
    texto_xml = limpar_xml(texto_xml)

    try:
        raiz = ET.fromstring(texto_xml)
    except ET.ParseError as e:
        print("Erro ao interpretar XML:", e)
        print("Linha:", e.position[0])
        print("Coluna:", e.position[1])

        linhas = texto_xml.splitlines()
        linha_erro = e.position[0]

        if 1 <= linha_erro <= len(linhas):
            linha = linhas[linha_erro - 1]
            print(f"Linha {linha_erro}:")
            print("BRUTO:", repr(linha))

            print("Caracteres (posição, repr, ord, hex):")
            for i, ch in enumerate(linha):
                print(f"{i:02d}: {repr(ch):6} | ord={ord(ch):3} | hex={ord(ch):02X}")

        return {}

    return _elemento_para_dict(raiz, ignorar_namespaces)


def limpar_xml(texto_xml: str) -> str:
    def escapar_texto(correspondencia):
        texto = correspondencia.group(1)
        texto = texto.replace("&", "&amp;")
        texto = texto.replace("<", "&lt;")
        texto = texto.replace(">", "&gt;")
        return f">{texto}<"

    return re.sub(r">([^<]+)<", escapar_texto, texto_xml)


def _limpar_tag(tag: str, ignorar_namespaces: bool) -> str:
    """
    Remove namespace de tags e atributos quando solicitado.
    Ex:
    {http://www.w3.org/2001/XMLSchema-instance}type -> type
    {http://schemas.xmlsoap.org/soap/envelope/}Body -> Body
    """
    if ignorar_namespaces and "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def _elemento_para_dict(elemento, ignorar_namespaces: bool = False):
    dict_tag = {}

    # atributos
    for chave, valor in elemento.attrib.items():
        chave = _limpar_tag(chave, ignorar_namespaces)
        dict_tag[chave] = valor

    filhos = list(elemento)

    # filhos
    for filho in filhos:
        dict_filho = _elemento_para_dict(filho, ignorar_namespaces)

        if dict_filho is None:
            continue

        tag = _limpar_tag(filho.tag, ignorar_namespaces)

        if tag in dict_tag:
            if not isinstance(dict_tag[tag], list):
                dict_tag[tag] = [dict_tag[tag]]

            dict_tag[tag].append(dict_filho)
        else:
            dict_tag[tag] = dict_filho

    texto = (elemento.text or "").strip()

    if texto:
        if filhos or elemento.attrib:
            dict_tag["#text"] = texto
        else:
            return texto

    # simplifica valores que possuem apenas texto + atributo type
    if "#text" in dict_tag and ("type" in dict_tag or not elemento.attrib):
        return dict_tag["#text"]

    # valor simples vazio com apenas atributo type
    if not filhos and not texto and list(dict_tag.keys()) == ["type"]:
        return ""

    if not dict_tag:
        return None

    return dict_tag


def __serializar(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return obj.total_seconds()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (bytes, bytearray, memoryview)):
        return base64.b64encode(bytes(obj)).decode()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Tipo {type(obj)} não serializável")


def __ocultar_subcorpos(obj):
    if isinstance(obj, dict):
        return {k: (__ocultar_subcorpos(v) if k != "subbodies" else None) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [__ocultar_subcorpos(item) for item in obj]
    return obj
