import base64
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID


def encode_base64_to_bytes(text: str) -> str:
    return base64.b64decode(text)


def decode_bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def decode_base64_to_string(base64_data: str) -> str:
    bytes_data = base64.b64decode(base64_data)

    return bytes_data.decode("utf-8")


def dict_to_string(obj):
    json_str = json.dumps(obj, default=__serializer, ensure_ascii=False)
    return json_str.encode("utf-8").decode("utf-8")


def string_to_dict(string: str, hide_subbodies: bool = False):
    data = json.loads(string)

    if hide_subbodies:
        data = __hide_subbodies(data)

    return data


def xml_to_dict(xml_string: str, ignore_namespaces: bool = False) -> dict:
    xml_string = clean_xml(xml_string)

    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        print("Erro ao parsear XML:", e)
        print("Linha:", e.position[0])
        print("Coluna:", e.position[1])

        lines = xml_string.splitlines()
        error_line = e.position[0]

        if 1 <= error_line <= len(lines):
            line = lines[error_line - 1]
            print(f"Linha {error_line}:")
            print("RAW:", repr(line))

            print("Caracteres (posição, repr, ord, hex):")
            for i, ch in enumerate(line):
                print(f"{i:02d}: {repr(ch):6} | ord={ord(ch):3} | hex={ord(ch):02X}")

        return {}

    return _elem_to_dict(root, ignore_namespaces)


def clean_xml(xml_string: str) -> str:
    def escape_text(match):
        text = match.group(1)
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return f">{text}<"

    return re.sub(r">([^<]+)<", escape_text, xml_string)


def _clean_tag(tag: str, ignore_namespaces: bool) -> str:
    """
    Remove namespace de tags e atributos quando solicitado.
    Ex:
    {http://www.w3.org/2001/XMLSchema-instance}type -> type
    {http://schemas.xmlsoap.org/soap/envelope/}Body -> Body
    """
    if ignore_namespaces and "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def _elem_to_dict(elem, ignore_namespaces: bool = False):
    tag_dict = {}

    # atributos
    for k, v in elem.attrib.items():
        k = _clean_tag(k, ignore_namespaces)
        tag_dict[k] = v

    children = list(elem)

    # filhos
    for child in children:
        child_dict = _elem_to_dict(child, ignore_namespaces)

        if child_dict is None:
            continue

        tag = _clean_tag(child.tag, ignore_namespaces)

        if tag in tag_dict:
            if not isinstance(tag_dict[tag], list):
                tag_dict[tag] = [tag_dict[tag]]

            tag_dict[tag].append(child_dict)
        else:
            tag_dict[tag] = child_dict

    text = (elem.text or "").strip()

    if text:
        if children or elem.attrib:
            tag_dict["#text"] = text
        else:
            return text

    # simplifica valores que possuem apenas texto + atributo type
    if "#text" in tag_dict and ("type" in tag_dict or not elem.attrib):
        return tag_dict["#text"]

    # Valor simples vazio com apenas atributo type
    if not children and not text and list(tag_dict.keys()) == ["type"]:
        return ""

    if not tag_dict:
        return None

    return tag_dict


def __serializer(obj):
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
    raise TypeError(f"Type {type(obj)} not serializable")


def __hide_subbodies(obj):
    if isinstance(obj, dict):
        return {k: (__hide_subbodies(v) if k != "subbodies" else None) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [__hide_subbodies(item) for item in obj]
    return obj
