from app.config.constants import ACCESS_TOKEN_COOKIE


def _payload(**overrides):
    base = {"nome": "Alice", "email": "alice@test.com", "senha": "senha1234"}
    base.update(overrides)
    return base


class TestSignup:
    def test_cria_usuario_e_seta_cookie(self, client):
        res = client.post("/auth/signup", json=_payload())

        assert res.status_code == 200
        body = res.json()
        assert body["email"] == "alice@test.com"
        assert body["ativo"] is True
        assert "token" not in body  # token só via cookie
        assert ACCESS_TOKEN_COOKIE in res.cookies

    def test_email_duplicado_da_409(self, client):
        client.post("/auth/signup", json=_payload())
        res = client.post("/auth/signup", json=_payload(nome="Outro"))

        assert res.status_code == 409

    def test_senha_curta_rejeitada_pelo_pydantic(self, client):
        res = client.post("/auth/signup", json=_payload(senha="123"))

        assert res.status_code == 422


class TestLogin:
    def test_credencial_valida(self, client):
        client.post("/auth/signup", json=_payload())
        # reseta cookies pra garantir que o login é quem seta
        client.cookies.clear()

        res = client.post(
            "/auth/login",
            json={"email": "alice@test.com", "senha": "senha1234"},
        )

        assert res.status_code == 200
        assert ACCESS_TOKEN_COOKIE in res.cookies

    def test_senha_errada_da_401(self, client):
        client.post("/auth/signup", json=_payload())
        client.cookies.clear()

        res = client.post(
            "/auth/login",
            json={"email": "alice@test.com", "senha": "errada00"},
        )

        assert res.status_code == 401

    def test_usuario_inexistente_da_401(self, client):
        res = client.post(
            "/auth/login",
            json={"email": "nao@existe.com", "senha": "senha1234"},
        )

        assert res.status_code == 401


class TestMe:
    def test_sem_cookie_da_401(self, client):
        res = client.get("/auth/me")
        assert res.status_code == 401

    def test_com_cookie_retorna_usuario(self, client):
        client.post("/auth/signup", json=_payload())

        res = client.get("/auth/me")

        assert res.status_code == 200
        assert res.json()["email"] == "alice@test.com"


class TestLogout:
    def test_apaga_cookie_e_bloqueia_me(self, client):
        client.post("/auth/signup", json=_payload())

        logout = client.post("/auth/logout")
        assert logout.status_code == 204

        # cookie foi expirado; TestClient descarta na próxima call
        me = client.get("/auth/me")
        assert me.status_code == 401
