from app.config.constants import COOKIE_TOKEN_ACESSO


def _payload(**sobrescritas):
    base = {"nome": "Alice", "email": "alice@test.com", "senha": "senha1234"}
    base.update(sobrescritas)
    return base


class TestCadastro:
    def test_cria_usuario_e_grava_cookie(self, api):
        res = api.post("/conta/cadastro", json=_payload())

        assert res.status_code == 200
        corpo = res.json()
        assert corpo["email"] == "alice@test.com"
        assert corpo["ativo"] is True
        assert "token" not in corpo  # token só via cookie
        assert COOKIE_TOKEN_ACESSO in res.cookies

    def test_email_duplicado_da_409(self, api):
        api.post("/conta/cadastro", json=_payload())
        res = api.post("/conta/cadastro", json=_payload(nome="Outro"))

        assert res.status_code == 409

    def test_senha_curta_rejeitada_pelo_pydantic(self, api):
        res = api.post("/conta/cadastro", json=_payload(senha="123"))

        assert res.status_code == 422


class TestEntrar:
    def test_credencial_valida(self, api):
        api.post("/conta/cadastro", json=_payload())
        # limpa os cookies para garantir que é o entrar quem grava
        api.cookies.clear()

        res = api.post(
            "/conta/entrar",
            json={"email": "alice@test.com", "senha": "senha1234"},
        )

        assert res.status_code == 200
        assert COOKIE_TOKEN_ACESSO in res.cookies

    def test_senha_errada_da_401(self, api):
        api.post("/conta/cadastro", json=_payload())
        api.cookies.clear()

        res = api.post(
            "/conta/entrar",
            json={"email": "alice@test.com", "senha": "errada00"},
        )

        assert res.status_code == 401

    def test_usuario_inexistente_da_401(self, api):
        res = api.post(
            "/conta/entrar",
            json={"email": "nao@existe.com", "senha": "senha1234"},
        )

        assert res.status_code == 401


class TestObterConta:
    def test_sem_cookie_da_401(self, api):
        res = api.get("/conta")
        assert res.status_code == 401

    def test_com_cookie_retorna_usuario(self, api):
        api.post("/conta/cadastro", json=_payload())

        res = api.get("/conta")

        assert res.status_code == 200
        assert res.json()["email"] == "alice@test.com"
        assert "criado_em" in res.json()


class TestSair:
    def test_apaga_cookie_e_bloqueia_conta(self, api):
        api.post("/conta/cadastro", json=_payload())

        sair = api.post("/conta/sair")
        assert sair.status_code == 204

        # cookie foi expirado; o TestClient descarta na próxima chamada
        conta = api.get("/conta")
        assert conta.status_code == 401
