import uuid

from fastapi import HTTPException, UploadFile, status

from app.config.constants import DIR_ARQUIVOS, ROTA_ARQUIVOS, TAMANHO_MAXIMO_IMAGEM_MB

TAMANHO_MAXIMO_BYTES = TAMANHO_MAXIMO_IMAGEM_MB * 1024 * 1024


def detectar_extensao_imagem(conteudo: bytes) -> str | None:
    """Identifica JPEG, PNG ou WebP pela assinatura do arquivo.

    Não confia no nome nem no Content-Type enviados pelo cliente.
    """
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "webp"
    return None


def salvar_imagem(arquivo: UploadFile, pasta: str) -> str:
    """Valida e grava a imagem em DIR_ARQUIVOS/<pasta>/<uuid>.<ext>.

    Devolve o caminho público (ex.: "/arquivos/fotos/3f2a….jpg") para guardar no banco.
    """
    # Lê só até 1 byte além do limite: suficiente para recusar sem carregar tudo.
    conteudo = arquivo.file.read(TAMANHO_MAXIMO_BYTES + 1)
    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"A imagem passa do limite de {TAMANHO_MAXIMO_IMAGEM_MB} MB",
        )
    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Arquivo vazio",
        )

    extensao = detectar_extensao_imagem(conteudo)
    if extensao is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato não suportado. Envie uma imagem JPG, PNG ou WebP",
        )

    nome = f"{uuid.uuid4().hex}.{extensao}"
    destino = DIR_ARQUIVOS / pasta
    destino.mkdir(parents=True, exist_ok=True)
    (destino / nome).write_bytes(conteudo)

    return f"{ROTA_ARQUIVOS}/{pasta}/{nome}"


def remover_arquivo(caminho_publico: str | None) -> None:
    """Apaga do disco um arquivo salvo por salvar_imagem. Ignora o que não for nosso."""
    if not caminho_publico or not caminho_publico.startswith(f"{ROTA_ARQUIVOS}/"):
        return

    relativo = caminho_publico.removeprefix(f"{ROTA_ARQUIVOS}/")
    alvo = (DIR_ARQUIVOS / relativo).resolve()
    # Nunca sai de DIR_ARQUIVOS, mesmo que o caminho venha com "..".
    if not alvo.is_relative_to(DIR_ARQUIVOS):
        return
    alvo.unlink(missing_ok=True)
