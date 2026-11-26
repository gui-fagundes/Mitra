"""Verificação de e-mail no cadastro (RF-ID-01)."""

import re

from app.models import Usuario
from app.utils.seguranca_utils import criar_token_sessao

SENHA = "senha1234"


def _cadastrar(api, email, nome="Ana Lima", papel="cliente"):
    api.post("/conta/sair")
    res = api.post(
        "/conta/cadastro",
        json={"nome": nome, "email": email, "senha": SENHA, "aceite_termos": True, "papel": papel},
    )
    assert res.status_code == 200
    return res.json()


def _token_do_email(email: dict) -> str:
    return re.search(r"verificar-email\?token=(\S+)", email["corpo"]).group(1)


class TestVerificacaoEmail:
    def test_cadastro_envia_link_e_comeca_sem_verificar(self, api, emails):
        conta = _cadastrar(api, "ana@test.com")

        assert conta["email_verificado_em"] is None
        assert len(emails) == 1
        assert emails[0]["para"] == "ana@test.com"
        assert "Confirme seu e-mail" in emails[0]["assunto"]
        assert "/verificar-email?token=" in emails[0]["corpo"]

    def test_link_confirma_o_email(self, api, emails):
        _cadastrar(api, "ana@test.com")

        res = api.post("/conta/email/verificar", json={"token": _token_do_email(emails[0])})

        assert res.status_code == 204
        assert api.get("/conta").json()["email_verificado_em"] is not None

    def test_link_funciona_sem_estar_logado_e_pode_ser_reaberto(self, api, emails):
        _cadastrar(api, "ana@test.com")
        token = _token_do_email(emails[0])
        api.post("/conta/sair")

        assert api.post("/conta/email/verificar", json={"token": token}).status_code == 204
        assert api.post("/conta/email/verificar", json={"token": token}).status_code == 204

    def test_token_invalido_ou_de_outra_finalidade(self, api):
        conta = _cadastrar(api, "ana@test.com")

        for token in ("lixo", criar_token_sessao(conta["idusuario"])):
            res = api.post("/conta/email/verificar", json={"token": token})
            assert res.status_code == 422
            assert "inválido ou expirado" in res.json()["detail"]

    def test_link_deixa_de_valer_se_o_email_mudar(self, api, sessao, emails):
        conta = _cadastrar(api, "ana@test.com")
        usuario = sessao.get(Usuario, conta["idusuario"])
        usuario.email = "ana.nova@test.com"
        sessao.commit()

        res = api.post("/conta/email/verificar", json={"token": _token_do_email(emails[0])})

        assert res.status_code == 422

    def test_reenviar_manda_outro_link(self, api, emails):
        _cadastrar(api, "ana@test.com")

        assert api.post("/conta/email/reenviar").status_code == 204
        assert len(emails) == 2
        assert (
            api.post(
                "/conta/email/verificar", json={"token": _token_do_email(emails[1])}
            ).status_code
            == 204
        )

    def test_reenviar_depois_de_verificado_da_409(self, api, emails):
        _cadastrar(api, "ana@test.com")
        api.post("/conta/email/verificar", json={"token": _token_do_email(emails[0])})

        assert api.post("/conta/email/reenviar").status_code == 409

    def test_reenviar_sem_login_da_401(self, api):
        assert api.post("/conta/email/reenviar").status_code == 401


class TestExigenciaDeEmailConfirmado:
    def test_sem_confirmar_nao_inicia_contato(self, api, emails, verificacao_obrigatoria):
        prestador = _cadastrar(api, "pedro@test.com", "Pedro Alves", "prestador")
        _cadastrar(api, "ana@test.com")

        res = api.post("/conversas", json={"idprestador": prestador["idusuario"], "texto": "Oi"})

        assert res.status_code == 403
        assert "Confirme seu e-mail" in res.json()["detail"]

    def test_depois_de_confirmar_inicia_contato(self, api, emails, verificacao_obrigatoria):
        prestador = _cadastrar(api, "pedro@test.com", "Pedro Alves", "prestador")
        _cadastrar(api, "ana@test.com")
        api.post("/conta/email/verificar", json={"token": _token_do_email(emails[-1])})

        res = api.post("/conversas", json={"idprestador": prestador["idusuario"], "texto": "Oi"})

        assert res.status_code == 201

    def test_sem_confirmar_nao_responde_mensagem(
        self, api, sessao, emails, verificacao_obrigatoria
    ):
        prestador = _cadastrar(api, "pedro@test.com", "Pedro Alves", "prestador")
        _cadastrar(api, "ana@test.com")
        api.post("/conta/email/verificar", json={"token": _token_do_email(emails[-1])})
        idconversa = api.post(
            "/conversas", json={"idprestador": prestador["idusuario"], "texto": "Oi"}
        ).json()["idconversa"]
        api.post("/conta/sair")
        api.post("/conta/entrar", json={"email": "pedro@test.com", "senha": SENHA})

        res = api.post(f"/conversas/{idconversa}/mensagens", json={"texto": "Olá"})

        assert res.status_code == 403

    def test_leitura_nao_exige_confirmacao(self, api, verificacao_obrigatoria):
        _cadastrar(api, "ana@test.com")

        assert api.get("/conversas").status_code == 200
        assert api.get("/conta").status_code == 200
