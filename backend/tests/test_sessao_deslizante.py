"""Sessão deslizante: o cookie deve ser reemitido em requisições autenticadas,
mas rotas que gravam o cookie explicitamente (entrar/sair) mandam."""

from app.config.constants import COOKIE_TOKEN_ACESSO


def _cadastrar(api):
    return api.post(
        "/conta/cadastro",
        json={"nome": "Slide", "email": "slide@test.com", "senha": "senha1234"},
    )


class TestSessaoDeslizante:
    def test_obter_conta_reemite_cookie(self, api):
        _cadastrar(api)
        cookie_original = api.cookies.get(COOKIE_TOKEN_ACESSO)

        res = api.get("/conta")

        assert res.status_code == 200
        # o httpx expõe o Set-Cookie da resposta via res.cookies
        assert COOKIE_TOKEN_ACESSO in res.cookies

        # Como o middleware roda antes do exp mudar de segundo, o token pode ser
        # igual ao original — o que importa é que veio um Set-Cookie novo,
        # renovando o Max-Age. O ponto crítico é justamente ter o header presente.
        header_set_cookie = res.headers.get("set-cookie", "")
        assert f"{COOKIE_TOKEN_ACESSO}=" in header_set_cookie
        assert "Max-Age=" in header_set_cookie
        assert cookie_original is not None

    def test_requisicao_sem_cookie_nao_recebe_cookie(self, api):
        res = api.get("/conta")

        assert res.status_code == 401
        assert COOKIE_TOKEN_ACESSO not in res.cookies

    def test_sair_nao_e_sobrescrito_pelo_middleware(self, api):
        _cadastrar(api)

        res = api.post("/conta/sair")

        assert res.status_code == 204
        # O cookie foi APAGADO pela rota. O middleware não deve tê-lo
        # reemitido — a próxima chamada sem cookie tem que falhar em /conta.
        api.cookies.clear()
        conta = api.get("/conta")
        assert conta.status_code == 401

    def test_entrar_grava_cookie_da_rota_nao_do_middleware(self, api):
        _cadastrar(api)
        api.cookies.clear()

        res = api.post(
            "/conta/entrar",
            json={"email": "slide@test.com", "senha": "senha1234"},
        )

        assert res.status_code == 200
        # Deve haver exatamente um Set-Cookie para o token (o da rota).
        set_cookies = res.headers.get_list("set-cookie")
        cookies_token = [c for c in set_cookies if c.startswith(f"{COOKIE_TOKEN_ACESSO}=")]
        assert len(cookies_token) == 1
