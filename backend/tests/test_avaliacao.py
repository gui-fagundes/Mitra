"""Avaliações: só o cliente, só depois da conclusão bilateral, até 30 dias; resposta
única do prestador; nada editável. Reflexos no perfil público e na busca."""

from datetime import timedelta

import pytest

from app.models import Contratacao, Servico
from app.services.avaliacao_services import nome_abreviado
from app.utils.data_utils import agora

SENHA = "senha1234"
CLIENTE = "cris@test.com"
PRESTADOR = "pedro@test.com"
TERCEIRO = "tina@test.com"


def _cadastrar(api, email, nome, papel="cliente"):
    api.post("/conta/sair")
    return api.post(
        "/conta/cadastro",
        json={"nome": nome, "email": email, "senha": SENHA, "aceite_termos": True, "papel": papel},
    ).json()


def _como(api, email):
    api.post("/conta/sair")
    api.cookies.clear()
    assert api.post("/conta/entrar", json={"email": email, "senha": SENHA}).status_code == 200


def _concluir_servico(api, idconversa, idservico, valor=240) -> int:
    """Proposta do cliente → aceite do prestador → conclusão dos dois.
    Começa e termina logado como o cliente."""
    idc = api.post(
        f"/conversas/{idconversa}/contratacoes",
        json={"idservico": idservico, "descricao": "Trocar tomadas"},
    ).json()["idcontratacao"]
    _como(api, PRESTADOR)
    api.post(f"/contratacoes/{idc}/aceitar")
    api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": valor})
    _como(api, CLIENTE)
    assert api.post(f"/contratacoes/{idc}/concluir", json={}).json()["estado"] == "concluido"
    return idc


@pytest.fixture()
def cenario(api, sessao):
    """Cris Souza (cliente) e Pedro (prestador) com um serviço concluído.
    Termina logado como Cris."""
    idservico = sessao.query(Servico).filter_by(slug="eletroeletronicos").one().idservico
    ids = {
        "prestador": _cadastrar(api, PRESTADOR, "Pedro", "prestador")["idusuario"],
        "terceiro": _cadastrar(api, TERCEIRO, "Tina")["idusuario"],
        "cliente": _cadastrar(api, CLIENTE, "Cris Souza")["idusuario"],
        "servico": idservico,
    }
    # Pedro precisa de um serviço na vitrine para aparecer na busca.
    _como(api, PRESTADOR)
    api.patch("/conta/vitrine", json={"servicos": [idservico]})
    _como(api, CLIENTE)
    ids["conversa"] = api.post(
        "/conversas", json={"idprestador": ids["prestador"], "texto": "Oi!"}
    ).json()["idconversa"]
    ids["contratacao"] = _concluir_servico(api, ids["conversa"], idservico)
    return ids


def _avaliar(api, idcontratacao, nota=5, comentario="Pontual e caprichoso."):
    return api.post(
        f"/contratacoes/{idcontratacao}/avaliacao", json={"nota": nota, "comentario": comentario}
    )


class TestAvaliar:
    def test_cliente_avalia_servico_concluido(self, api, cenario):
        res = _avaliar(api, cenario["contratacao"])

        assert res.status_code == 201
        avaliacao = res.json()
        assert avaliacao["nota"] == 5
        assert avaliacao["autor"] == "Cris S."
        assert avaliacao["servico"] == "Eletroeletrônicos"
        assert avaliacao["resposta"] is None

    def test_vira_evento_na_conversa_e_some_das_pendencias(self, api, cenario):
        url = f"/contratacoes/{cenario['contratacao']}"
        assert api.get(url).json()["aguardando_voce"] is True
        assert api.get(url).json()["pode_avaliar"] is True

        _avaliar(api, cenario["contratacao"], nota=4)

        contratacao = api.get(url).json()
        assert contratacao["aguardando_voce"] is False
        assert contratacao["pode_avaliar"] is False
        assert contratacao["avaliacao"]["nota"] == 4
        mensagens = api.get(f"/conversas/{cenario['conversa']}/mensagens").json()["itens"]
        assert mensagens[-1]["texto"] == "Cris Souza avaliou o serviço (4★)"

    def test_comentario_e_opcional(self, api, cenario):
        res = api.post(f"/contratacoes/{cenario['contratacao']}/avaliacao", json={"nota": 3})

        assert res.status_code == 201
        assert res.json()["comentario"] is None

    def test_comentario_em_branco_vira_nulo(self, api, cenario):
        assert _avaliar(api, cenario["contratacao"], comentario="   ").json()["comentario"] is None

    @pytest.mark.parametrize(
        "corpo", [{"nota": 0}, {"nota": 6}, {"nota": 5, "comentario": "x" * 1001}]
    )
    def test_entrada_invalida_da_422(self, api, cenario, corpo):
        res = api.post(f"/contratacoes/{cenario['contratacao']}/avaliacao", json=corpo)

        assert res.status_code == 422

    def test_nao_avalia_duas_vezes(self, api, cenario):
        _avaliar(api, cenario["contratacao"])

        assert _avaliar(api, cenario["contratacao"], nota=1).status_code == 409

    def test_prestador_nao_avalia(self, api, cenario):
        _como(api, PRESTADOR)

        assert _avaliar(api, cenario["contratacao"]).status_code == 403

    def test_terceiro_nao_avalia(self, api, cenario):
        _como(api, TERCEIRO)

        assert _avaliar(api, cenario["contratacao"]).status_code == 403

    def test_so_depois_de_concluido(self, api, cenario):
        aberta = api.post(
            f"/conversas/{cenario['conversa']}/contratacoes",
            json={"idservico": cenario["servico"], "descricao": "Outro serviço"},
        ).json()["idcontratacao"]

        assert _avaliar(api, aberta).status_code == 422

    def test_prazo_de_30_dias(self, api, cenario, sessao):
        contratacao = sessao.get(Contratacao, cenario["contratacao"])
        contratacao.concluido_em = agora() - timedelta(days=31)
        sessao.commit()

        assert api.get(f"/contratacoes/{cenario['contratacao']}").json()["pode_avaliar"] is False
        res = _avaliar(api, cenario["contratacao"])
        assert res.status_code == 422
        assert "prazo" in res.json()["detail"]


class TestResponder:
    def _avaliado(self, api, cenario) -> int:
        idavaliacao = _avaliar(api, cenario["contratacao"], nota=4).json()["idavaliacao"]
        _como(api, PRESTADOR)
        return idavaliacao

    def test_prestador_responde_uma_vez(self, api, cenario):
        idavaliacao = self._avaliado(api, cenario)
        assert api.get(f"/contratacoes/{cenario['contratacao']}").json()["pode_responder"] is True

        res = api.post(f"/avaliacoes/{idavaliacao}/resposta", json={"texto": " Obrigado, Cris! "})

        assert res.status_code == 200
        assert res.json()["resposta"] == "Obrigado, Cris!"
        assert res.json()["resposta_em"] is not None
        segunda = api.post(f"/avaliacoes/{idavaliacao}/resposta", json={"texto": "De novo"})
        assert segunda.status_code == 409
        assert api.get(f"/contratacoes/{cenario['contratacao']}").json()["aguardando_voce"] is False

    def test_cliente_nao_responde(self, api, cenario):
        idavaliacao = _avaliar(api, cenario["contratacao"]).json()["idavaliacao"]

        res = api.post(f"/avaliacoes/{idavaliacao}/resposta", json={"texto": "Eu mesma"})

        assert res.status_code == 403

    def test_resposta_vazia_da_422(self, api, cenario):
        idavaliacao = self._avaliado(api, cenario)

        res = api.post(f"/avaliacoes/{idavaliacao}/resposta", json={"texto": "   "})

        assert res.status_code == 422

    def test_avaliacao_inexistente_da_404(self, api, cenario):
        assert api.post("/avaliacoes/999999/resposta", json={"texto": "x"}).status_code == 404


class TestListaPublica:
    def test_lista_com_media_e_respostas(self, api, cenario):
        idavaliacao = _avaliar(api, cenario["contratacao"], nota=5).json()["idavaliacao"]
        _concluir_servico(api, cenario["conversa"], cenario["servico"])
        segunda = api.get("/contratacoes", params={"estado": "concluido"}).json()[0]
        _avaliar(api, segunda["idcontratacao"], nota=4, comentario="Bom")
        _como(api, PRESTADOR)
        api.post(f"/avaliacoes/{idavaliacao}/resposta", json={"texto": "Valeu!"})
        api.post("/conta/sair")
        api.cookies.clear()  # lista pública

        pagina = api.get(f"/prestadores/{cenario['prestador']}/avaliacoes").json()

        assert pagina["total"] == 2
        assert pagina["nota_media"] == 4.5
        assert [a["nota"] for a in pagina["itens"]] == [4, 5]  # mais recente primeiro
        assert pagina["itens"][1]["resposta"] == "Valeu!"

        uma = api.get(
            f"/prestadores/{cenario['prestador']}/avaliacoes",
            params={"limite": 1, "deslocamento": 1},
        ).json()
        assert [a["nota"] for a in uma["itens"]] == [5]

    def test_quem_nao_e_prestador_da_404(self, api, cenario):
        assert api.get(f"/prestadores/{cenario['cliente']}/avaliacoes").status_code == 404


class TestReflexos:
    def test_perfil_publico_mostra_nota_e_quantidade(self, api, cenario):
        url = f"/prestadores/{cenario['prestador']}"
        assert api.get(url).json()["nota_media"] is None

        _avaliar(api, cenario["contratacao"], nota=4)

        perfil = api.get(url).json()
        assert perfil["nota_media"] == 4.0
        assert perfil["qtd_avaliacoes"] == 1

    def test_busca_filtra_ordena_e_destaca(self, api, cenario):
        # Paula: prestadora com vitrine mas sem avaliação.
        _cadastrar(api, "paula@test.com", "Paula", "prestador")
        api.patch("/conta/vitrine", json={"servicos": [cenario["servico"]]})
        _como(api, CLIENTE)
        _avaliar(api, cenario["contratacao"], nota=5, comentario="Excelente trabalho")

        filtrado = api.get("/prestadores", params={"nota_min": 4}).json()
        assert [i["nome"] for i in filtrado["itens"]] == ["Pedro"]

        melhor = api.get("/prestadores", params={"ordem": "melhor"}).json()["itens"]
        assert [i["nome"] for i in melhor] == ["Pedro", "Paula"]
        assert melhor[0]["nota_media"] == 5.0
        assert melhor[0]["qtd_avaliacoes"] == 1
        assert melhor[0]["destaque"] == "Excelente trabalho"
        assert melhor[1]["destaque"] is None

    def test_reputacao_pesa_a_nota(self, api, cenario):
        _cadastrar(api, "paula@test.com", "Paula", "prestador")
        api.patch("/conta/vitrine", json={"servicos": [cenario["servico"]]})
        _como(api, CLIENTE)
        _avaliar(api, cenario["contratacao"], nota=5)

        # Os dois acessaram agora (mesma atividade): a nota decide.
        nomes = [i["nome"] for i in api.get("/prestadores").json()["itens"]]
        assert nomes == ["Pedro", "Paula"]


class TestNomeAbreviado:
    @pytest.mark.parametrize(
        ("nome", "esperado"),
        [("Cristina Souza Lima", "Cristina L."), ("Cris", "Cris"), ("ana maria", "ana M.")],
    )
    def test_abrevia(self, nome, esperado):
        assert nome_abreviado(nome) == esperado
