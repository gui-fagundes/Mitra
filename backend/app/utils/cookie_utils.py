from fastapi import Response

from app.config.constants import (
    ACCESS_TOKEN_COOKIE,
    IS_PRODUCTION,
    TOKEN_EXPIRATION_TIME,
)


def set_auth_cookie(response: Response, token: str) -> None:
    """Grava o token JWT como cookie httpOnly."""
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=TOKEN_EXPIRATION_TIME * 60,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
        secure=IS_PRODUCTION,
        samesite="lax",
    )
