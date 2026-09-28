"""CNPJ do prestador: dígitos verificadores (inclusive alfanumérico), consulta à
BrasilAPI e gravação só de CNPJ ativo."""

import httpx
import pytest

from app.utils import cnpj_utils
from app.utils.cnpj_utils import ResultadoConsulta, SituacaoConsulta

# Válidos: Banco do Brasil e o exemplo oficial da Receita para CNPJ alfanumérico.
CNPJ_NUMERICO = "00000000000191"
CNPJ_ALFANUMERICO = "12ABC34501DE35"
CNPJ_OUTRO = "11222333000181"

URL = "/conta/vitrine/cnpj"


class TestDigitosVerificadores:
    @pytest.mark.parametrize("cnpj", [CNPJ_NUMERICO, CNPJ_ALFANUMERICO, CNPJ_OUTRO])
    def test_aceita_validos(self, cnpj):
        assert cnpj_utils.dv_valido(cnpj)

    @pytest.mark.parametrize(
        "cnpj",
        [
            "00000000000192",  # dígito errado
            "12ABC34501DE36",  # dígito errado (alfanumérico)
            "11111111111111",  # todos iguais
            "0000000000019",  # curto
            "12ABC34501DEAB",  # dígitos verificadores com letra
            "12.ABC.345/01DE-35",  # sem normalizar
        ],
    )
    def test_recusa_invalidos(self, cnpj):
        assert not cnpj_utils.dv_valido(cnpj)

    def test_normaliza_mascara_e_minusculas(self):
        assert cnpj_utils.normalizar(" 12.abc.345/01de-35 ") == CNPJ_ALFANUMERICO
        assert cnpj_utils.normalizar("00.000.000/0001-91") == CNPJ_NUMERICO


def _cliente_falso(responder):
    return httpx.Client(transport=httpx.MockTransport(responder))


class TestConsultaNaReceita:
    def test_ativo(self):
        cliente = _cliente_falso(
            lambda r: httpx.Response(
                200,
                json={
                    "situacao_cadastral": 2,
                    "descricao_situacao_cadastral": "ATIVA",
                    "razao_social": "BANCO DO BRASIL SA",
                },
            )
        )

        resultado = cnpj_utils.consultar_na_receita(CNPJ_NUMERICO, cliente)

        assert resultado.situacao is SituacaoConsulta.ATIVO
        assert resultado.razao_social == "BANCO DO BRASIL SA"

    def test_inativo(self):
        cliente = _cliente_falso(
            lambda r: httpx.Response(
                200, json={"situacao_cadastral": 8, "descricao_situacao_cadastral": "BAIXADA"}
            )
        )

        resultado = cnpj_utils.consultar_na_receita(CNPJ_NUMERICO, cliente)

        assert resultado.situacao is SituacaoConsulta.INATIVO
        assert resultado.descricao_situacao == "BAIXADA"

    def test_inexistente(self):
        cliente = _cliente_falso(lambda r: httpx.Response(404, json={"type": "not_found"}))

        resultado = cnpj_utils.consultar_na_receita(CNPJ_NUMERICO, cliente)

        assert resultado.situacao is SituacaoConsulta.INEXISTENTE

    @pytest.mark.parametrize("status", [429, 500, 502])
    def test_erro_do_servico_vira_indisponivel(self, status):
        cliente = _cliente_falso(lambda r: httpx.Response(status))

        assert (
            cnpj_utils.consultar_na_receita(CNPJ_NUMERICO, cliente).situacao
            is SituacaoConsulta.INDISPONIVEL
        )

    def test_timeout_vira_indisponivel(self):
        def estourar(request):
            raise httpx.ConnectTimeout("demorou", request=request)

        resultado = cnpj_utils.consultar_na_receita(CNPJ_NUMERICO, _cliente_falso(estourar))

        assert resultado.situacao is SituacaoConsulta.INDISPONIVEL

    def test_consulta_a_url_da_brasilapi(self):
        urls = []

        def registrar(request):
            urls.append(str(request.url))
            return httpx.Response(404)

        cnpj_utils.consultar_na_receita(CNPJ_ALFANUMERICO, _cliente_falso(registrar))

        assert urls == [f"https://brasilapi.com.br/api/cnpj/v1/{CNPJ_ALFANUMERICO}"]


@pytest.fixture()
def receita(monkeypatch):
    """Troca a consulta real por uma resposta configurável; registra os CNPJs consultados."""

    class Receita:
        resultado = ResultadoConsulta(SituacaoConsulta.ATIVO, "ATIVA", "EMPRESA TESTE LTDA")
        consultados: list[str] = []

        def __call__(self, cnpj, cliente=None):
            self.consultados.append(cnpj)
            return self.resultado

    falsa = Receita()
    falsa.consultados = []
    monkeypatch.setattr(cnpj_utils, "consultar_na_receita", falsa)
    return falsa


def _cadastrar(api, email="joao@test.com", papel="prestador"):
    return api.post(
        "/conta/cadastro",
        json={
            "nome": "João",
            "email": email,
            "senha": "senha1234",
            "aceite_termos": True,
            "papel": papel,
        },
    ).json()


class TestCadastrarCnpj:
    def test_cnpj_ativo_e_gravado_e_da_o_selo(self, api, receita):
        usuario = _cadastrar(api)

        res = api.put(URL, json={"cnpj": "00.000.000/0001-91"})

        assert res.status_code == 200
        corpo = res.json()
        assert corpo["cnpj"] == CNPJ_NUMERICO
        assert corpo["cnpj_validado"] is True
        assert corpo["cnpj_validado_em"]
        assert receita.consultados == [CNPJ_NUMERICO]
        publico = api.get(f"/prestadores/{usuario['idusuario']}").json()
        assert publico["cnpj_validado"] is True
        assert "cnpj" not in publico  # o público vê só o selo

    def test_aceita_alfanumerico_em_minusculas(self, api, receita):
        _cadastrar(api)

        res = api.put(URL, json={"cnpj": "12.abc.345/01de-35"})

        assert res.status_code == 200
        assert res.json()["cnpj"] == CNPJ_ALFANUMERICO

    def test_digito_invalido_nem_consulta_a_receita(self, api, receita):
        _cadastrar(api)

        res = api.put(URL, json={"cnpj": "00.000.000/0001-92"})

        assert res.status_code == 422
        assert receita.consultados == []

    def test_inexistente_na_receita_nao_grava(self, api, receita):
        _cadastrar(api)
        receita.resultado = ResultadoConsulta(SituacaoConsulta.INEXISTENTE)

        res = api.put(URL, json={"cnpj": CNPJ_NUMERICO})

        assert res.status_code == 422
        assert "não encontrado" in res.json()["detail"]
        assert api.get("/conta/vitrine").json()["cnpj"] is None

    def test_inativo_na_receita_nao_grava(self, api, receita):
        _cadastrar(api)
        receita.resultado = ResultadoConsulta(SituacaoConsulta.INATIVO, "BAIXADA")

        res = api.put(URL, json={"cnpj": CNPJ_NUMERICO})

        assert res.status_code == 422
        assert "baixada" in res.json()["detail"]
        assert api.get("/conta/vitrine").json()["cnpj_validado"] is False

    def test_receita_fora_do_ar_da_503_e_nao_grava(self, api, receita):
        _cadastrar(api)
        receita.resultado = ResultadoConsulta(SituacaoConsulta.INDISPONIVEL)

        res = api.put(URL, json={"cnpj": CNPJ_NUMERICO})

        assert res.status_code == 503
        assert api.get("/conta/vitrine").json()["cnpj"] is None

    def test_cnpj_de_outro_prestador_da_409_sem_consultar(self, api, receita):
        _cadastrar(api)
        api.put(URL, json={"cnpj": CNPJ_NUMERICO})
        api.post("/conta/sair")
        _cadastrar(api, email="maria@test.com")
        receita.consultados.clear()

        res = api.put(URL, json={"cnpj": CNPJ_NUMERICO})

        assert res.status_code == 409
        assert receita.consultados == []

    def test_reenviar_o_proprio_cnpj_revalida(self, api, receita):
        _cadastrar(api)
        api.put(URL, json={"cnpj": CNPJ_NUMERICO})

        assert api.put(URL, json={"cnpj": CNPJ_NUMERICO}).status_code == 200

    def test_trocar_por_outro_cnpj(self, api, receita):
        _cadastrar(api)
        api.put(URL, json={"cnpj": CNPJ_NUMERICO})

        res = api.put(URL, json={"cnpj": CNPJ_OUTRO})

        assert res.json()["cnpj"] == CNPJ_OUTRO

    def test_cliente_sem_vitrine_da_404(self, api, receita):
        _cadastrar(api, papel="cliente")

        assert api.put(URL, json={"cnpj": CNPJ_NUMERICO}).status_code == 404

    def test_sem_login_da_401(self, api, receita):
        assert api.put(URL, json={"cnpj": CNPJ_NUMERICO}).status_code == 401


class TestRemoverCnpj:
    def test_remove_e_tira_o_selo(self, api, receita):
        usuario = _cadastrar(api)
        api.put(URL, json={"cnpj": CNPJ_NUMERICO})

        res = api.delete(URL)

        assert res.status_code == 200
        assert res.json()["cnpj"] is None
        assert res.json()["cnpj_validado"] is False
        assert api.get(f"/prestadores/{usuario['idusuario']}").json()["cnpj_validado"] is False
