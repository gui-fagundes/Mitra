from datetime import timedelta

from fastapi import Request
from jose import JWTError

from app.config.constants import COOKIE_TOKEN_ACESSO, MINUTOS_EXPIRACAO_TOKEN
from app.utils.cookie_utils import gravar_cookie_sessao
from app.utils.data_utils import agora
from app.utils.seguranca_utils import criar_token, decodificar_token


async def renovar_sessao(requisicao: Request, proximo):
    """Se a requisição chega com um token válido, reemite o cookie com exp
    renovado. Assim o usuário só é deslogado após X minutos de inatividade.

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

    if not payload or "sub" not in payload:
        return resposta

    nova_expiracao = agora() + timedelta(minutes=MINUTOS_EXPIRACAO_TOKEN)
    novo_token = criar_token({"sub": payload["sub"], "exp": int(nova_expiracao.timestamp())})
    gravar_cookie_sessao(resposta, novo_token)

    return resposta
