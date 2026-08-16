from datetime import timedelta

from fastapi import Request
from jose import JWTError

from app.config.constants import ACCESS_TOKEN_COOKIE, TOKEN_EXPIRATION_TIME
from app.utils.auth_utils import criar_token, decrypt_token
from app.utils.cookie_utils import set_auth_cookie
from app.utils.datetime_utils import get_now


async def sliding_session_middleware(request: Request, call_next):
    """Se a request chega com um access_token válido, reemite o cookie com exp
    resetado. Assim o usuário só é deslogado após X minutos de inatividade.

    Respeita endpoints que setaram o cookie explicitamente (login/logout): se
    a response já tem um Set-Cookie para access_token, não sobrescreve.
    """
    incoming_token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    response = await call_next(request)

    if not incoming_token:
        return response

    ja_setou_cookie = any(
        h.startswith(f"{ACCESS_TOKEN_COOKIE}=") for h in response.headers.getlist("set-cookie")
    )
    if ja_setou_cookie:
        return response

    try:
        payload = decrypt_token(incoming_token)
    except JWTError:
        return response

    if not payload or "sub" not in payload:
        return response

    novo_exp = get_now() + timedelta(minutes=TOKEN_EXPIRATION_TIME)
    novo_token = criar_token({"sub": payload["sub"], "exp": int(novo_exp.timestamp())})
    set_auth_cookie(response, novo_token)

    return response
