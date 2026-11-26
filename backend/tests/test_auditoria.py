"""Auditoria de ações sensíveis e contexto da requisição (RF-AD-02, RNF-DI-02)."""

import re
from datetime import timedelta

import pytest
from fastapi import Depends

from app.middlewares import contexto_requisicao
from app.models import Auditoria, LogErro, Usuario
from app.models.auditoria_model import (
    CNPJ_DEFINIR,
    CNPJ_REMOVER,
    CONTA_CADASTRAR,
    CONTA_ENTRAR,
    CONTA_ENTRAR_FALHOU,
    DADOS_EXPORTAR,
    EMAIL_VERIFICAR,
    SENHA_REDEFINIR,
    SENHA_SOLICITAR,
)
from app.services import auditoria_services
from app.utils import cnpj_utils
from app.utils.cnpj_utils import ResultadoConsulta, SituacaoConsulta
from app.utils.data_utils import agora

SENHA = "senha1234"
EMAIL = "ana@test.com"
CNPJ = "00000000000191"


def _cadastrar(api, email=EMAIL, papel="cliente", **cabecalhos):
    api.post("/conta/sair")
    res = api.post(
        "/conta/cadastro",
        json={
            "nome": "Ana Lima",
            "email": email,
            "senha": SENHA,
            "aceite_termos": True,
            "papel": papel,
        },
        headers=cabecalhos,
    )
    assert res.status_code == 200
    return res


def _registros(sessao, acao=None):
    consulta = sessao.query(Auditoria).order_by(Auditoria.idauditoria)
    if acao:
        consulta = consulta.filter(Auditoria.acao == acao)
    return consulta.all()


def _sem_segredos(registro: Auditoria):
    texto = str(registro.dados or "")
    assert SENHA not in texto
    assert "senha_hash" not in texto
    assert "token" not in texto


class TestContextoDaRequisicao:
    def test_devolve_x_request_id(self, api):
        res = api.get("/saude")

        assert re.fullmatch(r"[0-9a-f]{32}", res.headers["X-Request-ID"])

    def test_reaproveita_id_valido_recebido(self, api):
        res = api.get("/saude", headers={"X-Request-ID": "abc-123.ok"})

        assert res.headers["X-Request-ID"] == "abc-123.ok"

    def test_troca_id_recebido_invalido(self, api):
        res = api.get("/saude", headers={"X-Request-ID": "<script>" + "x" * 80})

        assert re.fullmatch(r"[0-9a-f]{32}", res.headers["X-Request-ID"])

    def test_cadastro_registra_ip_e_id_da_requisicao(self, api, sessao):
        res = _cadastrar(api)

        registro = _registros(sessao, CONTA_CADASTRAR)[0]
        assert registro.idrequisicao == res.headers["X-Request-ID"]
        assert registro.ip == "testclient"

    def test_x_forwarded_for_ignorado_por_padrao(self, api, sessao):
        _cadastrar(api, **{"X-Forwarded-For": "203.0.113.9"})

        assert _registros(sessao, CONTA_CADASTRAR)[0].ip == "testclient"

    def test_x_forwarded_for_vale_atras_de_proxy(self, api, sessao, monkeypatch):
        monkeypatch.setattr(contexto_requisicao, "CONFIAR_X_FORWARDED_FOR", True)

        _cadastrar(api, **{"X-Forwarded-For": "203.0.113.9, 10.0.0.1"})

        assert _registros(sessao, CONTA_CADASTRAR)[0].ip == "203.0.113.9"


class TestAcoesDaConta:
    def test_cadastro(self, api, sessao):
        conta = _cadastrar(api, papel="prestador").json()

        registro = _registros(sessao, CONTA_CADASTRAR)[0]
        assert registro.idusuario == conta["idusuario"]
        assert (registro.entidade, registro.identidade) == ("usuario", conta["idusuario"])
        assert registro.dados == {"papel": "prestador"}
        _sem_segredos(registro)

    def test_entrar(self, api, sessao):
        conta = _cadastrar(api).json()
        api.post("/conta/sair")

        api.post("/conta/entrar", json={"email": EMAIL, "senha": SENHA})

        assert [r.idusuario for r in _registros(sessao, CONTA_ENTRAR)] == [conta["idusuario"]]

    def test_senha_errada_e_registrada_mesmo_com_401(self, api, sessao):
        conta = _cadastrar(api).json()
        api.post("/conta/sair")

        res = api.post("/conta/entrar", json={"email": EMAIL, "senha": "errada123"})

        assert res.status_code == 401
        registro = _registros(sessao, CONTA_ENTRAR_FALHOU)[0]
        assert registro.idusuario == conta["idusuario"]
        assert registro.dados == {"email": EMAIL, "motivo": "senha incorreta"}
        assert "errada123" not in str(registro.dados)

    def test_email_inexistente_fica_sem_usuario(self, api, sessao):
        api.post("/conta/entrar", json={"email": "ninguem@test.com", "senha": SENHA})

        registro = _registros(sessao, CONTA_ENTRAR_FALHOU)[0]
        assert registro.idusuario is None
        assert registro.dados["motivo"] == "e-mail não cadastrado"

    def test_conta_inativa(self, api, sessao):
        conta = _cadastrar(api).json()
        sessao.get(Usuario, conta["idusuario"]).ativo = False
        sessao.commit()
        api.post("/conta/sair")

        api.post("/conta/entrar", json={"email": EMAIL, "senha": SENHA})

        assert _registros(sessao, CONTA_ENTRAR_FALHOU)[0].dados["motivo"] == "conta inativa"

    def test_redefinicao_de_senha(self, api, sessao, emails):
        _cadastrar(api)
        api.post("/conta/sair")
        api.post("/conta/senha/esqueci", json={"email": "ninguem@test.com"})
        assert _registros(sessao, SENHA_SOLICITAR) == []  # e-mail sem conta não registra

        api.post("/conta/senha/esqueci", json={"email": EMAIL})
        token = re.search(r"token=(\S+)", emails[-1]["corpo"]).group(1)
        api.post("/conta/senha/redefinir", json={"token": token, "nova_senha": "outra-senha-9"})

        assert len(_registros(sessao, SENHA_SOLICITAR)) == 1
        registro = _registros(sessao, SENHA_REDEFINIR)[0]
        _sem_segredos(registro)
        assert "outra-senha-9" not in str(registro.dados)

    def test_verificacao_de_email_registra_uma_vez(self, api, sessao, emails):
        _cadastrar(api)
        token = re.search(r"token=(\S+)", emails[0]["corpo"]).group(1)

        api.post("/conta/email/verificar", json={"token": token})
        api.post("/conta/email/verificar", json={"token": token})

        assert len(_registros(sessao, EMAIL_VERIFICAR)) == 1

    def test_exportacao_registra_e_traz_os_acessos(self, api, sessao):
        _cadastrar(api)

        dados = api.get("/conta/exportar").json()

        assert len(_registros(sessao, DADOS_EXPORTAR)) == 1
        acoes = [a["acao"] for a in dados["acessos"]]
        assert acoes == [CONTA_CADASTRAR, DADOS_EXPORTAR]
        assert set(dados["acessos"][0]) == {"acao", "em", "ip"}


@pytest.fixture()
def receita_ativa(monkeypatch):
    monkeypatch.setattr(
        cnpj_utils,
        "consultar_na_receita",
        lambda cnpj, cliente=None: ResultadoConsulta(
            SituacaoConsulta.ATIVO, "ATIVA", "EMPRESA LTDA"
        ),
    )


class TestCnpj:
    def test_definir_e_remover(self, api, sessao, receita_ativa):
        _cadastrar(api, papel="prestador")

        api.put("/conta/vitrine/cnpj", json={"cnpj": CNPJ})
        api.delete("/conta/vitrine/cnpj")

        definir = _registros(sessao, CNPJ_DEFINIR)[0]
        remover = _registros(sessao, CNPJ_REMOVER)[0]
        assert definir.entidade == "prestador_perfil"
        assert definir.dados == {"cnpj": [None, CNPJ]}
        assert remover.dados == {"cnpj": [CNPJ, None]}

    def test_remover_sem_cnpj_nao_registra(self, api, sessao):
        _cadastrar(api, papel="prestador")

        api.delete("/conta/vitrine/cnpj")

        assert _registros(sessao, CNPJ_REMOVER) == []


class TestGuarda:
    def test_registro_desfeito_junto_com_a_acao(self, sessao):
        auditoria_services.registrar(sessao, CONTA_ENTRAR)
        sessao.rollback()

        assert _registros(sessao) == []

    def test_exclusao_da_conta_mantem_o_registro_sem_usuario(self, api, sessao):
        conta = _cadastrar(api).json()
        sessao.delete(sessao.get(Usuario, conta["idusuario"]))
        sessao.commit()
        sessao.expire_all()

        registro = _registros(sessao, CONTA_CADASTRAR)[0]
        assert registro.idusuario is None

    def test_expurgo_respeita_os_prazos(self, sessao):
        momento = agora()
        sessao.add_all(
            [
                Auditoria(acao=CONTA_ENTRAR, criado_em=momento - timedelta(days=400)),
                Auditoria(acao=CONTA_ENTRAR, criado_em=momento - timedelta(days=30)),
                LogErro(
                    rota="/x", metodo="GET", erro="e", ocorrido_em=momento - timedelta(days=100)
                ),
                LogErro(
                    rota="/x", metodo="GET", erro="e", ocorrido_em=momento - timedelta(days=10)
                ),
            ]
        )
        sessao.commit()

        assert auditoria_services.expurgar(sessao) == (1, 1)
        assert len(_registros(sessao)) == 1
        assert sessao.query(LogErro).count() == 1


ROTA_QUE_QUEBRA = "/_teste/quebra-logado"


@pytest.fixture()
def rota_logada_que_quebra():
    from app.config.dependencies import obter_usuario_logado
    from main import app

    def quebrar(usuario=Depends(obter_usuario_logado)):
        return 1 / 0

    app.add_api_route(ROTA_QUE_QUEBRA, quebrar, methods=["GET"])
    yield
    app.router.routes[:] = [
        r for r in app.router.routes if getattr(r, "path", None) != ROTA_QUE_QUEBRA
    ]


class TestLogErroLigadoARequisicao:
    def test_erro_500_guarda_id_ip_e_usuario(self, api, sessao, rota_logada_que_quebra):
        conta = _cadastrar(api).json()

        res = api.get(ROTA_QUE_QUEBRA)

        assert res.status_code == 500
        registro = sessao.query(LogErro).filter_by(rota=ROTA_QUE_QUEBRA).one()
        assert registro.idrequisicao == res.headers["X-Request-ID"]
        assert registro.ip == "testclient"
        assert registro.idusuario == conta["idusuario"]
