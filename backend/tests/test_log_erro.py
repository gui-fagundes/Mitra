"""Log de erros (RF-AD-02): exceção não tratada vira 500 padronizado e é gravada em
logerro com repr + traceback; erros de domínio (4xx) não são gravados."""

import pytest

from app.middlewares.tratamento_erros import TAMANHO_MAXIMO_ERRO, _descrever
from app.models import LogErro

ROTA_QUE_QUEBRA = "/_teste/quebra"


@pytest.fixture()
def rota_que_quebra():
    from main import app

    def quebrar():
        return 1 / 0

    app.add_api_route(ROTA_QUE_QUEBRA, quebrar, methods=["GET"])
    yield
    app.router.routes[:] = [
        r for r in app.router.routes if getattr(r, "path", None) != ROTA_QUE_QUEBRA
    ]


class TestLogErro:
    def test_erro_nao_tratado_vira_500_e_e_registrado(self, api, sessao, rota_que_quebra):
        res = api.get(ROTA_QUE_QUEBRA)

        assert res.status_code == 500
        assert res.json() == {
            "detail": "Ocorreu um erro inesperado no servidor. Tente novamente mais tarde."
        }
        registro = sessao.query(LogErro).filter_by(rota=ROTA_QUE_QUEBRA).one()
        assert registro.metodo == "GET"
        assert registro.erro.startswith("ZeroDivisionError(")
        assert "Traceback" in registro.erro
        assert registro.ocorrido_em is not None

    def test_erro_de_dominio_nao_e_registrado(self, api, sessao):
        antes = sessao.query(LogErro).count()

        assert api.get("/conversas/999999").status_code == 401  # sem login
        assert api.get("/prestadores/999999").status_code == 404

        assert sessao.query(LogErro).count() == antes


class TestDescrever:
    def test_trunca_no_meio_quando_passa_do_limite(self):
        try:
            raise ValueError("x" * (TAMANHO_MAXIMO_ERRO * 2))
        except ValueError as e:
            texto = _descrever(e)

        assert "caracteres omitidos" in texto
        assert len(texto) < TAMANHO_MAXIMO_ERRO + 200
        assert texto.startswith("ValueError(")
