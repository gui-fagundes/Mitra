from fastapi import Request
from jose import JWTError

from app.config.constants import COOKIE_TOKEN_ACESSO
from app.utils.cookie_utils import gravar_cookie_sessao
from app.utils.seguranca_utils import criar_token_sessao, decodificar_token, e_token_de_sessao


async def renovar_sessao(requisicao: Request, proximo):
    """Se a requisição chega com um token de sessão válido, reemite o cookie com
    exp renovado. Assim o usuário só é deslogado após X minutos de inatividade.

    Respeita rotas que gravaram o cookie explicitamente (entrar/sair): se a
    resposta já tem um Set-Cookie para o token, não sobrescreve.
    """
    token_recebido = requisicao.cookies.get(COOKIE_TOKEN_ACESSO)

    resposta = await proximo(requisicao)

    if not token_recebido:
        return resposta

    ja_gravou_cookie = any(
        h.startswith(f"{COOKIE_TOKEN_ACESSO}=") for h in resposta.headers.getlist("set-cookie")
    )
    if ja_gravou_cookie:
        return resposta

    try:
        payload = decodificar_token(token_recebido)
    except JWTError:
        return resposta

    if not e_token_de_sessao(payload):
        return resposta

    gravar_cookie_sessao(resposta, criar_token_sessao(payload["sub"]))

    return resposta
