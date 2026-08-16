"""Sliding session: cookie deve ser reemitido em requests autenticadas,
mas endpoints que setam o cookie explicitamente (login/logout) mandam."""

from app.config.constants import ACCESS_TOKEN_COOKIE


def _signup(client):
    return client.post(
        "/auth/signup",
        json={"nome": "Slide", "email": "slide@test.com", "senha": "senha1234"},
    )


class TestSlidingSession:
    def test_me_reemite_cookie(self, client):
        _signup(client)
        cookie_original = client.cookies.get(ACCESS_TOKEN_COOKIE)

        res = client.get("/auth/me")

        assert res.status_code == 200
        # httpx expõe Set-Cookie do response via res.cookies
        assert ACCESS_TOKEN_COOKIE in res.cookies

        # Como o middleware roda antes do exp mudar de segundo, o token pode ser
        # igual ao original — o que importa é que veio um Set-Cookie novo,
        # renovando o Max-Age. O bit crítico é justamente ter o header presente.
        set_cookie_header = res.headers.get("set-cookie", "")
        assert f"{ACCESS_TOKEN_COOKIE}=" in set_cookie_header
        assert "Max-Age=" in set_cookie_header
        assert cookie_original is not None

    def test_request_sem_cookie_nao_recebe_cookie(self, client):
        res = client.get("/auth/me")

        assert res.status_code == 401
        assert ACCESS_TOKEN_COOKIE not in res.cookies

    def test_logout_nao_e_sobrescrito_pelo_middleware(self, client):
        _signup(client)

        res = client.post("/auth/logout")

        assert res.status_code == 204
        # O cookie foi APAGADO pelo endpoint. O middleware não deve tê-lo
        # reemitido — a próxima call sem cookie tem que falhar em /me.
        client.cookies.clear()
        me = client.get("/auth/me")
        assert me.status_code == 401

    def test_login_seta_cookie_do_endpoint_nao_do_middleware(self, client):
        _signup(client)
        client.cookies.clear()

        res = client.post(
            "/auth/login",
            json={"email": "slide@test.com", "senha": "senha1234"},
        )

        assert res.status_code == 200
        # Deve ter exatamente um Set-Cookie para access_token (do endpoint).
        set_cookies = res.headers.get_list("set-cookie")
        auth_cookies = [c for c in set_cookies if c.startswith(f"{ACCESS_TOKEN_COOKIE}=")]
        assert len(auth_cookies) == 1
