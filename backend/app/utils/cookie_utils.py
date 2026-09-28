from fastapi import Response

from app.config.constants import (
    COOKIE_TOKEN_ACESSO,
    EM_PRODUCAO,
    MINUTOS_EXPIRACAO_TOKEN,
)


def gravar_cookie_sessao(resposta: Response, token: str) -> None:
    """Grava o token JWT como cookie httpOnly."""
    resposta.set_cookie(
        key=COOKIE_TOKEN_ACESSO,
        value=token,
        max_age=MINUTOS_EXPIRACAO_TOKEN * 60,
        httponly=True,
        secure=EM_PRODUCAO,
        samesite="lax",
        path="/",
    )


def apagar_cookie_sessao(resposta: Response) -> None:
    resposta.delete_cookie(
        key=COOKIE_TOKEN_ACESSO,
        path="/",
        secure=EM_PRODUCAO,
        samesite="lax",
    )
