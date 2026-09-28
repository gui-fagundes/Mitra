"""Contratação dentro da conversa: proposta → combinado (aceite bilateral) →
concluido (conclusão bilateral com preço cobrado) | cancelado."""

import pytest

from app.models import Servico

SENHA = "senha1234"
CLIENTE = "cris@test.com"
PRESTADOR = "pedro@test.com"
TERCEIRO = "tina@test.com"


def _cadastrar(api, email, papel="cliente"):
    api.post("/conta/sair")
    return api.post(
        "/conta/cadastro",
        json={
            "nome": email.split("@")[0].title(),
            "email": email,
            "senha": SENHA,
            "aceite_termos": True,
            "papel": papel,
        },
    ).json()


def _como(api, email):
    api.post("/conta/sair")
    api.cookies.clear()
    assert api.post("/conta/entrar", json={"email": email, "senha": SENHA}).status_code == 200


@pytest.fixture()
def cenario(api, sessao):
    """Cris (cliente) iniciou conversa com Pedro (prestador); Tina é terceira.
    Termina logado como Cris."""
    ids = {
        "prestador": _cadastrar(api, PRESTADOR, "prestador")["idusuario"],
        "terceiro": _cadastrar(api, TERCEIRO)["idusuario"],
        "cliente": _cadastrar(api, CLIENTE)["idusuario"],
    }
    ids["conversa"] = api.post(
        "/conversas", json={"idprestador": ids["prestador"], "texto": "Oi, Pedro!"}
    ).json()["idconversa"]
    ids["servico"] = sessao.query(Servico).filter_by(slug="eletroeletronicos").one().idservico
    return ids


def _propor(api, cenario, **extra):
    corpo = {
        "idservico": cenario["servico"],
        "descricao": "Trocar duas tomadas da cozinha",
        "local": "Cassino, Rio Grande",
        "data_prevista": "2026-10-05",
        "valor_estimado": 200,
        **extra,
    }
    return api.post(f"/conversas/{cenario['conversa']}/contratacoes", json=corpo)


def _eventos(api, idconversa):
    itens = api.get(f"/conversas/{idconversa}/mensagens").json()["itens"]
    return [m["texto"] for m in itens if m["tipo"] == "evento"]


def _combinado(api, cenario) -> int:
    """Proposta do cliente aceita pelo prestador. Termina logado como o prestador."""
    idc = _propor(api, cenario).json()["idcontratacao"]
    _como(api, PRESTADOR)
    assert api.post(f"/contratacoes/{idc}/aceitar").json()["estado"] == "combinado"
    return idc


class TestProposta:
    def test_cliente_propoe(self, api, cenario):
        res = _propor(api, cenario)

        assert res.status_code == 201
        c = res.json()
        assert c["estado"] == "proposta"
        assert c["papel"] == "cliente"
        assert c["idproponente"] == cenario["cliente"]
        assert c["servico"]["slug"] == "eletroeletronicos"
        assert c["valor_estimado"] == 200.0
        assert c["aceite_cliente_em"] is not None  # quem propõe já aceita
        assert c["aceite_prestador_em"] is None
        assert c["aguardando_voce"] is False
        assert _eventos(api, cenario["conversa"]) == ["Cris propôs um serviço: Eletroeletrônicos"]

    def test_prestador_tambem_propoe(self, api, cenario):
        _como(api, PRESTADOR)

        c = _propor(api, cenario, valor_estimado=240).json()

        assert c["papel"] == "prestador"
        assert c["aceite_prestador_em"] is not None
        assert c["aceite_cliente_em"] is None

    def test_evento_aponta_para_a_contratacao(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]

        itens = api.get(f"/conversas/{cenario['conversa']}/mensagens").json()["itens"]

        assert itens[-1]["tipo"] == "evento"
        assert itens[-1]["idcontratacao"] == idc

    def test_so_uma_aberta_por_conversa(self, api, cenario):
        _propor(api, cenario)

        assert _propor(api, cenario).status_code == 409

    def test_opcionais_podem_faltar(self, api, cenario):
        res = api.post(
            f"/conversas/{cenario['conversa']}/contratacoes",
            json={"idservico": cenario["servico"], "descricao": "Orçamento"},
        )

        assert res.status_code == 201
        assert res.json()["valor_estimado"] is None

    @pytest.mark.parametrize(
        "extra",
        [{"idservico": 999999}, {"descricao": ""}, {"descricao": "   "}, {"valor_estimado": -1}],
    )
    def test_proposta_invalida_da_422(self, api, cenario, extra):
        assert _propor(api, cenario, **extra).status_code == 422

    def test_terceiro_nao_propoe_nem_ve(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]
        _como(api, TERCEIRO)

        assert _propor(api, cenario).status_code == 403
        assert api.get(f"/contratacoes/{idc}").status_code == 403
        assert api.post(f"/contratacoes/{idc}/aceitar").status_code == 403
        assert api.get("/contratacoes").json() == []


class TestNegociacao:
    def test_aceite_dos_dois_combina_o_plano(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]
        _como(api, PRESTADOR)
        assert api.get(f"/contratacoes/{idc}").json()["aguardando_voce"] is True

        c = api.post(f"/contratacoes/{idc}/aceitar").json()

        assert c["estado"] == "combinado"
        assert c["combinado_em"] is not None
        assert _eventos(api, cenario["conversa"])[-1] == (
            "Plano combinado: os dois aceitaram a proposta"
        )

    def test_aceitar_de_novo_da_409(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]

        assert api.post(f"/contratacoes/{idc}/aceitar").status_code == 409

    def test_editar_zera_o_aceite_do_outro(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]
        _como(api, PRESTADOR)

        c = api.patch(f"/contratacoes/{idc}", json={"valor_estimado": 260}).json()

        assert c["estado"] == "proposta"
        assert c["valor_estimado"] == 260.0
        assert c["aceite_prestador_em"] is not None
        assert c["aceite_cliente_em"] is None
        assert _eventos(api, cenario["conversa"])[-1] == "Pedro alterou a proposta"

        _como(api, CLIENTE)
        assert api.post(f"/contratacoes/{idc}/aceitar").json()["estado"] == "combinado"

    def test_editar_sem_mudar_nada_nao_gera_evento(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]
        _como(api, PRESTADOR)

        c = api.patch(f"/contratacoes/{idc}", json={"valor_estimado": 200}).json()

        assert c["aceite_cliente_em"] is not None
        assert len(_eventos(api, cenario["conversa"])) == 1

    def test_descricao_nula_da_422(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]

        assert api.patch(f"/contratacoes/{idc}", json={"descricao": None}).status_code == 422

    def test_nao_edita_depois_de_combinado(self, api, cenario):
        idc = _combinado(api, cenario)

        assert api.patch(f"/contratacoes/{idc}", json={"local": "Centro"}).status_code == 409


class TestConclusao:
    def test_conclusao_bilateral_com_preco_cobrado(self, api, cenario):
        idc = _combinado(api, cenario)

        c = api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 240}).json()
        assert c["estado"] == "combinado"
        assert c["valor_final"] == 240.0
        assert c["conclusao_prestador_em"] is not None
        assert _eventos(api, cenario["conversa"])[-1] == "Pedro confirmou a conclusão (R$ 240,00)"

        _como(api, CLIENTE)
        c = api.post(f"/contratacoes/{idc}/concluir", json={}).json()

        assert c["estado"] == "concluido"
        assert c["concluido_em"] is not None
        assert _eventos(api, cenario["conversa"])[-1] == (
            "Serviço concluído (R$ 240,00): os dois confirmaram. A avaliação está liberada."
        )

    def test_mudar_o_preco_derruba_a_confirmacao_do_outro(self, api, cenario):
        idc = _combinado(api, cenario)
        api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 240})
        _como(api, CLIENTE)

        c = api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 220}).json()

        assert c["estado"] == "combinado"
        assert c["valor_final"] == 220.0
        assert c["conclusao_prestador_em"] is None
        assert c["conclusao_cliente_em"] is not None

        _como(api, PRESTADOR)
        assert api.post(f"/contratacoes/{idc}/concluir", json={}).json()["estado"] == "concluido"

    def test_primeira_confirmacao_exige_o_preco(self, api, cenario):
        idc = _combinado(api, cenario)

        assert api.post(f"/contratacoes/{idc}/concluir", json={}).status_code == 422

    def test_confirmar_de_novo_da_409(self, api, cenario):
        idc = _combinado(api, cenario)
        api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 240})

        assert api.post(f"/contratacoes/{idc}/concluir", json={}).status_code == 409

    def test_nao_conclui_proposta_nao_combinada(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]

        res = api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 100})

        assert res.status_code == 409


class TestCancelamento:
    def test_recusar_proposta(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]
        _como(api, PRESTADOR)

        c = api.post(f"/contratacoes/{idc}/cancelar", json={"motivo": "Não atendo aos domingos"})

        assert c.json()["estado"] == "cancelado"
        assert c.json()["idcancelado_por"] == cenario["prestador"]
        assert _eventos(api, cenario["conversa"])[-1] == (
            "Pedro recusou a proposta: Não atendo aos domingos"
        )

    def test_cancelar_servico_combinado(self, api, cenario):
        idc = _combinado(api, cenario)

        api.post(f"/contratacoes/{idc}/cancelar", json={})

        assert _eventos(api, cenario["conversa"])[-1] == "Pedro cancelou o serviço"

    def test_nao_cancela_concluido(self, api, cenario):
        idc = _combinado(api, cenario)
        api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 240})
        _como(api, CLIENTE)
        api.post(f"/contratacoes/{idc}/concluir", json={})

        assert api.post(f"/contratacoes/{idc}/cancelar", json={}).status_code == 409

    def test_depois_de_cancelar_pode_propor_de_novo(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]
        api.post(f"/contratacoes/{idc}/cancelar", json={})

        assert _propor(api, cenario).status_code == 201

    def test_chat_continua_depois_de_cancelar(self, api, cenario):
        idc = _propor(api, cenario).json()["idcontratacao"]
        api.post(f"/contratacoes/{idc}/cancelar", json={})

        res = api.post(f"/conversas/{cenario['conversa']}/mensagens", json={"texto": "Ok!"})

        assert res.status_code == 201


class TestListagens:
    def test_minhas_por_papel_e_estado(self, api, cenario):
        idc = _combinado(api, cenario)

        como_prestador = api.get("/contratacoes", params={"papel": "prestador"}).json()
        assert [c["idcontratacao"] for c in como_prestador] == [idc]
        assert api.get("/contratacoes", params={"papel": "cliente"}).json() == []
        assert api.get("/contratacoes", params={"estado": "proposta"}).json() == []

        _como(api, CLIENTE)
        como_cliente = api.get("/contratacoes", params={"papel": "cliente"}).json()
        assert como_cliente[0]["outra_parte"]["nome"] == "Pedro"
        assert como_cliente[0]["papel"] == "cliente"

    def test_historico_da_conversa(self, api, cenario):
        primeira = _propor(api, cenario).json()["idcontratacao"]
        api.post(f"/contratacoes/{primeira}/cancelar", json={})
        segunda = _propor(api, cenario).json()["idcontratacao"]

        historico = api.get(f"/conversas/{cenario['conversa']}/contratacoes").json()

        assert [c["idcontratacao"] for c in historico] == [segunda, primeira]

    def test_estado_invalido_da_422(self, api, cenario):
        assert api.get("/contratacoes", params={"estado": "pago"}).status_code == 422


class TestReflexos:
    def _concluir(self, api, cenario):
        idc = _combinado(api, cenario)
        api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 240})
        _como(api, CLIENTE)
        api.post(f"/contratacoes/{idc}/concluir", json={})

    def test_perfil_publico_conta_servicos_concluidos(self, api, cenario):
        url = f"/prestadores/{cenario['prestador']}"
        assert api.get(url).json()["servicos_concluidos"] == 0

        self._concluir(api, cenario)

        assert api.get(url).json()["servicos_concluidos"] == 1

    def test_busca_ja_contratado(self, api, cenario, sessao):
        # Pedro precisa de um serviço para aparecer na busca.
        _como(api, PRESTADOR)
        api.patch("/conta/vitrine", json={"servicos": [cenario["servico"]]})
        _como(api, CLIENTE)
        assert api.get("/prestadores", params={"ja_contratado": True}).json()["total"] == 0

        self._concluir(api, cenario)

        resultado = api.get("/prestadores", params={"ja_contratado": True}).json()
        assert [i["nome"] for i in resultado["itens"]] == ["Pedro"]
