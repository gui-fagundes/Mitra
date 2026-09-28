"""Esqueci minha senha: token stateless de uso único enviado por e-mail."""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app.config.constants import COOKIE_TOKEN_ACESSO, FINALIDADE_TOKEN_REDEFINIR_SENHA
from app.models import Usuario
from app.services.conta_services import _impressao_senha
from app.utils import email_utils
from app.utils.data_utils import agora
from app.utils.seguranca_utils import criar_token, criar_token_sessao

EMAIL = "bia@test.com"
SENHA = "senha1234"


@pytest.fixture()
def emails(monkeypatch):
    """Troca o envio real por uma lista com os e-mails que seriam enviados."""
    enviados = []

    async def _coletar(para, assunto, corpo_texto, corpo_html=None):
        enviados.append({"para": para, "assunto": assunto, "texto": corpo_texto})

    monkeypatch.setattr(email_utils, "enviar_email", _coletar)
    return enviados


@pytest.fixture()
def usuario(api):
    api.post(
        "/conta/cadastro",
        json={"nome": "Bia", "email": EMAIL, "senha": SENHA, "aceite_termos": True},
    )
    api.cookies.clear()


def _token_do_email(email: dict) -> str:
    link = next(p for p in email["texto"].split() if "/redefinir-senha?token=" in p)
    return parse_qs(urlparse(link).query)["token"][0]


def _pedir_token(api, emails) -> str:
    api.post("/conta/senha/esqueci", json={"email": EMAIL})
    return _token_do_email(emails[-1])


def _entrar(api, senha):
    return api.post("/conta/entrar", json={"email": EMAIL, "senha": senha})


class TestEsqueciSenha:
    def test_envia_email_com_link(self, api, usuario, emails):
        res = api.post("/conta/senha/esqueci", json={"email": EMAIL})

        assert res.status_code == 204
        assert len(emails) == 1
        assert emails[0]["para"] == EMAIL
        assert "Olá, Bia." in emails[0]["texto"]
        assert _token_do_email(emails[0])

    def test_email_inexistente_responde_igual_e_nao_envia(self, api, emails):
        res = api.post("/conta/senha/esqueci", json={"email": "ninguem@test.com"})

        assert res.status_code == 204
        assert emails == []

    def test_usuario_inativo_nao_recebe(self, api, usuario, emails, sessao):
        sessao.query(Usuario).filter_by(email=EMAIL).one().ativo = False
        sessao.commit()

        res = api.post("/conta/senha/esqueci", json={"email": EMAIL})

        assert res.status_code == 204
        assert emails == []

    def test_email_malformado_da_422(self, api, emails):
        res = api.post("/conta/senha/esqueci", json={"email": "nao-e-email"})

        assert res.status_code == 422


class TestRedefinirSenha:
    def test_troca_a_senha(self, api, usuario, emails):
        token = _pedir_token(api, emails)

        res = api.post("/conta/senha/redefinir", json={"token": token, "nova_senha": "novasenha99"})

        assert res.status_code == 204
        assert _entrar(api, "novasenha99").status_code == 200
        assert _entrar(api, SENHA).status_code == 401

    def test_token_so_vale_uma_vez(self, api, usuario, emails):
        token = _pedir_token(api, emails)
        api.post("/conta/senha/redefinir", json={"token": token, "nova_senha": "novasenha99"})

        res = api.post(
            "/conta/senha/redefinir", json={"token": token, "nova_senha": "outrasenha99"}
        )

        assert res.status_code == 422
        assert _entrar(api, "novasenha99").status_code == 200

    def test_trocar_a_senha_invalida_tokens_anteriores(self, api, usuario, emails):
        antigo = _pedir_token(api, emails)
        novo = _pedir_token(api, emails)
        api.post("/conta/senha/redefinir", json={"token": novo, "nova_senha": "novasenha99"})

        res = api.post(
            "/conta/senha/redefinir", json={"token": antigo, "nova_senha": "outrasenha99"}
        )

        assert res.status_code == 422

    def test_token_expirado_da_422(self, api, usuario, sessao):
        conta = sessao.query(Usuario).filter_by(email=EMAIL).one()
        expirado = criar_token(
            {
                "sub": str(conta.idusuario),
                "finalidade": FINALIDADE_TOKEN_REDEFINIR_SENHA,
                "impressao": _impressao_senha(conta),
                "exp": int((agora() - timedelta(minutes=1)).timestamp()),
            }
        )

        res = api.post(
            "/conta/senha/redefinir", json={"token": expirado, "nova_senha": "novasenha99"}
        )

        assert res.status_code == 422

    def test_token_de_sessao_nao_serve_para_redefinir(self, api, usuario, sessao):
        conta = sessao.query(Usuario).filter_by(email=EMAIL).one()

        res = api.post(
            "/conta/senha/redefinir",
            json={"token": criar_token_sessao(conta.idusuario), "nova_senha": "novasenha99"},
        )

        assert res.status_code == 422

    def test_token_adulterado_da_422(self, api, usuario, emails):
        token = _pedir_token(api, emails)

        res = api.post(
            "/conta/senha/redefinir", json={"token": token[:-4] + "abcd", "nova_senha": "x" * 10}
        )

        assert res.status_code == 422

    def test_nova_senha_curta_da_422(self, api, usuario, emails):
        token = _pedir_token(api, emails)

        res = api.post("/conta/senha/redefinir", json={"token": token, "nova_senha": "123"})

        assert res.status_code == 422


class TestFinalidadeDoToken:
    def test_token_de_redefinicao_nao_vale_como_sessao(self, api, usuario, emails):
        token = _pedir_token(api, emails)
        api.cookies.set(COOKIE_TOKEN_ACESSO, token)

        res = api.get("/conta")

        assert res.status_code == 401
        # e o middleware não o "promove" a sessão reemitindo o cookie
        assert COOKIE_TOKEN_ACESSO not in res.cookies
