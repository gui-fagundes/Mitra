from datetime import timedelta

from app.config.constants import COOKIE_TOKEN_ACESSO
from app.models import Cidade, Usuario
from app.utils.data_utils import agora


def _payload(**sobrescritas):
    base = {
        "nome": "Alice",
        "email": "alice@test.com",
        "senha": "senha1234",
        "aceite_termos": True,
    }
    base.update(sobrescritas)
    return base


def _rio_grande(sessao) -> Cidade:
    return sessao.query(Cidade).filter_by(nome="Rio Grande", uf="RS").one()


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

    def test_sem_aceite_dos_termos_da_422(self, api):
        res = api.post("/conta/cadastro", json=_payload(aceite_termos=False))

        assert res.status_code == 422

    def test_aceite_dos_termos_e_obrigatorio(self, api):
        payload = _payload()
        del payload["aceite_termos"]

        res = api.post("/conta/cadastro", json=payload)

        assert res.status_code == 422

    def test_grava_momento_do_aceite(self, api):
        res = api.post("/conta/cadastro", json=_payload())

        assert res.json()["aceite_termos_em"] is not None

    def test_grava_cidade_e_telefone(self, api, sessao):
        cidade = _rio_grande(sessao)

        res = api.post(
            "/conta/cadastro",
            json=_payload(idcidade=cidade.idcidade, telefone=" (53) 99999-0000 "),
        )

        assert res.status_code == 200
        corpo = res.json()
        assert corpo["cidade"] == {"idcidade": cidade.idcidade, "nome": "Rio Grande", "uf": "RS"}
        assert corpo["telefone"] == "(53) 99999-0000"

    def test_cidade_e_telefone_sao_opcionais(self, api):
        res = api.post("/conta/cadastro", json=_payload(telefone="  "))

        assert res.status_code == 200
        assert res.json()["cidade"] is None
        assert res.json()["telefone"] is None

    def test_cidade_inexistente_da_422(self, api):
        res = api.post("/conta/cadastro", json=_payload(idcidade=999999))

        assert res.status_code == 422

    def test_cidade_inativa_da_422(self, api, sessao):
        cidade = _rio_grande(sessao)
        cidade.ativo = False
        sessao.commit()

        res = api.post("/conta/cadastro", json=_payload(idcidade=cidade.idcidade))

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
        corpo = res.json()
        assert corpo["email"] == "alice@test.com"
        assert "criado_em" in corpo
        assert corpo["notificar_email"] is True
        assert corpo["busca_somente_cnpj"] is False
        assert "senha_hash" not in corpo


class TestAtualizarConta:
    def test_sem_cookie_da_401(self, api):
        res = api.patch("/conta", json={"nome": "Nova"})
        assert res.status_code == 401

    def test_altera_nome_cidade_e_preferencias(self, api, sessao):
        api.post("/conta/cadastro", json=_payload())
        cidade = _rio_grande(sessao)

        res = api.patch(
            "/conta",
            json={
                "nome": "Alice Souza",
                "idcidade": cidade.idcidade,
                "notificar_email": False,
                "busca_somente_cnpj": True,
            },
        )

        assert res.status_code == 200
        corpo = res.json()
        assert corpo["nome"] == "Alice Souza"
        assert corpo["cidade"]["idcidade"] == cidade.idcidade
        assert corpo["notificar_email"] is False
        assert corpo["busca_somente_cnpj"] is True

    def test_campos_ausentes_nao_mudam(self, api):
        api.post("/conta/cadastro", json=_payload(telefone="53 9999"))

        res = api.patch("/conta", json={"nome": "Outro nome"})

        assert res.json()["telefone"] == "53 9999"

    def test_null_limpa_campos_opcionais(self, api, sessao):
        cidade = _rio_grande(sessao)
        api.post("/conta/cadastro", json=_payload(idcidade=cidade.idcidade, telefone="53 9999"))

        res = api.patch("/conta", json={"idcidade": None, "telefone": None})

        assert res.json()["cidade"] is None
        assert res.json()["telefone"] is None

    def test_nao_troca_email_nem_senha(self, api):
        api.post("/conta/cadastro", json=_payload())

        res = api.patch("/conta", json={"email": "outro@test.com", "senha": "novasenha1"})

        assert res.status_code == 200
        assert res.json()["email"] == "alice@test.com"
        api.cookies.clear()
        entrar = api.post("/conta/entrar", json={"email": "alice@test.com", "senha": "senha1234"})
        assert entrar.status_code == 200

    def test_nome_nulo_da_422(self, api):
        api.post("/conta/cadastro", json=_payload())

        res = api.patch("/conta", json={"nome": None})

        assert res.status_code == 422

    def test_nome_em_branco_da_422(self, api):
        api.post("/conta/cadastro", json=_payload())

        res = api.patch("/conta", json={"nome": "   "})

        assert res.status_code == 422

    def test_preferencia_nula_da_422(self, api):
        api.post("/conta/cadastro", json=_payload())

        res = api.patch("/conta", json={"notificar_email": None})

        assert res.status_code == 422

    def test_cidade_inexistente_da_422(self, api):
        api.post("/conta/cadastro", json=_payload())

        res = api.patch("/conta", json={"idcidade": 999999})

        assert res.status_code == 422


class TestUltimoAcesso:
    def _usuario(self, sessao) -> Usuario:
        return sessao.query(Usuario).filter_by(email="alice@test.com").one()

    def test_requisicao_autenticada_registra_acesso(self, api, sessao):
        api.post("/conta/cadastro", json=_payload())
        assert self._usuario(sessao).ultimo_acesso_em is None

        api.get("/conta")

        assert self._usuario(sessao).ultimo_acesso_em is not None

    def test_nao_regrava_dentro_do_intervalo(self, api, sessao):
        api.post("/conta/cadastro", json=_payload())
        api.get("/conta")
        primeiro = self._usuario(sessao).ultimo_acesso_em

        api.get("/conta")

        assert self._usuario(sessao).ultimo_acesso_em == primeiro

    def test_regrava_depois_do_intervalo(self, api, sessao):
        api.post("/conta/cadastro", json=_payload())
        usuario = self._usuario(sessao)
        antigo = agora() - timedelta(hours=1)
        usuario.ultimo_acesso_em = antigo
        sessao.commit()

        api.get("/conta")

        assert self._usuario(sessao).ultimo_acesso_em > antigo
