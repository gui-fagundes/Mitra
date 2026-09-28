"""Chat independente da contratação: iniciar contato, mensagens, acesso e paginação."""

import pytest

SENHA = "senha1234"


def _cadastrar(api, email, papel="cliente", nome=None):
    api.post("/conta/sair")
    return api.post(
        "/conta/cadastro",
        json={
            "nome": nome or email.split("@")[0].title(),
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
def pessoas(api):
    """Prestador, cliente e um terceiro; termina logado como o cliente."""
    ids = {
        "prestador": _cadastrar(api, "pedro@test.com", "prestador", "Pedro")["idusuario"],
        "terceiro": _cadastrar(api, "tina@test.com", nome="Tina")["idusuario"],
        "cliente": _cadastrar(api, "cris@test.com", nome="Cris")["idusuario"],
    }
    return ids


def _iniciar(api, idprestador, texto="Olá! Preciso de um orçamento."):
    return api.post("/conversas", json={"idprestador": idprestador, "texto": texto})


class TestIniciar:
    def test_cria_conversa_com_a_primeira_mensagem(self, api, pessoas):
        res = _iniciar(api, pessoas["prestador"])

        assert res.status_code == 201
        conversa = res.json()
        assert conversa["papel"] == "cliente"
        assert conversa["outra_parte"]["nome"] == "Pedro"
        assert conversa["ultima_mensagem"]["texto"] == "Olá! Preciso de um orçamento."
        assert conversa["ultima_mensagem"]["tipo"] == "texto"
        assert "email" not in conversa["outra_parte"]

    def test_segundo_contato_reaproveita_a_conversa(self, api, pessoas):
        primeira = _iniciar(api, pessoas["prestador"]).json()

        res = _iniciar(api, pessoas["prestador"], "Oi de novo")

        assert res.status_code == 200
        assert res.json()["idconversa"] == primeira["idconversa"]
        mensagens = api.get(f"/conversas/{primeira['idconversa']}/mensagens").json()["itens"]
        assert [m["texto"] for m in mensagens] == ["Olá! Preciso de um orçamento.", "Oi de novo"]

    def test_so_com_prestador(self, api, pessoas):
        assert _iniciar(api, pessoas["terceiro"]).status_code == 404
        assert _iniciar(api, 999999).status_code == 404

    def test_nao_consigo_mesmo(self, api, pessoas):
        _como(api, "pedro@test.com")

        assert _iniciar(api, pessoas["prestador"]).status_code == 422

    @pytest.mark.parametrize("texto", ["", "   ", "x" * 2001])
    def test_texto_invalido_da_422(self, api, pessoas, texto):
        assert _iniciar(api, pessoas["prestador"], texto).status_code == 422

    def test_sem_login_da_401(self, api, pessoas):
        api.post("/conta/sair")
        api.cookies.clear()

        assert _iniciar(api, pessoas["prestador"]).status_code == 401

    def test_prestador_tambem_pode_contratar_outro_prestador(self, api, pessoas):
        _cadastrar(api, "paula@test.com", "prestador", "Paula")
        ida = _iniciar(api, pessoas["prestador"]).json()

        # Pedro procurando Paula é outra conversa (outro par cliente/prestador).
        _como(api, "pedro@test.com")
        paula = [c for c in api.get("/conversas").json() if c["outra_parte"]["nome"] == "Paula"]
        volta = _iniciar(api, paula[0]["outra_parte"]["idusuario"]).json()

        assert volta["idconversa"] != ida["idconversa"]
        assert volta["papel"] == "cliente"


class TestListar:
    def test_prestador_ve_a_conversa_com_papel_prestador(self, api, pessoas):
        _iniciar(api, pessoas["prestador"])
        _como(api, "pedro@test.com")

        conversas = api.get("/conversas").json()

        assert len(conversas) == 1
        assert conversas[0]["papel"] == "prestador"
        assert conversas[0]["outra_parte"]["nome"] == "Cris"

    def test_mais_recente_primeiro(self, api, pessoas):
        _cadastrar(api, "paula@test.com", "prestador", "Paula")
        paula = api.get("/conta").json()["idusuario"]
        _como(api, "cris@test.com")
        com_pedro = _iniciar(api, pessoas["prestador"]).json()
        _iniciar(api, paula)

        api.post(f"/conversas/{com_pedro['idconversa']}/mensagens", json={"texto": "Novidade"})

        nomes = [c["outra_parte"]["nome"] for c in api.get("/conversas").json()]
        assert nomes == ["Pedro", "Paula"]

    def test_sem_conversas(self, api, pessoas):
        assert api.get("/conversas").json() == []


class TestAcesso:
    def test_terceiro_nao_le_nem_escreve(self, api, pessoas):
        idconversa = _iniciar(api, pessoas["prestador"]).json()["idconversa"]
        _como(api, "tina@test.com")

        assert api.get(f"/conversas/{idconversa}").status_code == 403
        assert api.get(f"/conversas/{idconversa}/mensagens").status_code == 403
        res = api.post(f"/conversas/{idconversa}/mensagens", json={"texto": "intrusa"})
        assert res.status_code == 403
        assert api.get("/conversas").json() == []

    def test_conversa_inexistente_da_404(self, api, pessoas):
        assert api.get("/conversas/999999").status_code == 404


class TestMensagens:
    def test_os_dois_lados_conversam(self, api, pessoas):
        idconversa = _iniciar(api, pessoas["prestador"], "Oi, Pedro").json()["idconversa"]
        _como(api, "pedro@test.com")
        res = api.post(f"/conversas/{idconversa}/mensagens", json={"texto": "  Oi, Cris!  "})

        assert res.status_code == 201
        assert res.json()["texto"] == "Oi, Cris!"
        mensagens = api.get(f"/conversas/{idconversa}/mensagens").json()["itens"]
        assert [(m["idautor"], m["texto"]) for m in mensagens] == [
            (pessoas["cliente"], "Oi, Pedro"),
            (pessoas["prestador"], "Oi, Cris!"),
        ]

    def test_paginacao_e_polling(self, api, pessoas):
        idconversa = _iniciar(api, pessoas["prestador"], "m1").json()["idconversa"]
        url = f"/conversas/{idconversa}/mensagens"
        for n in range(2, 6):
            api.post(url, json={"texto": f"m{n}"})

        recentes = api.get(url, params={"limite": 2}).json()
        assert [m["texto"] for m in recentes["itens"]] == ["m4", "m5"]
        assert recentes["tem_mais_antigas"] is True

        anteriores = api.get(
            url, params={"limite": 2, "antes_de": recentes["itens"][0]["idmensagem"]}
        ).json()
        assert [m["texto"] for m in anteriores["itens"]] == ["m2", "m3"]

        primeira = api.get(
            url, params={"limite": 2, "antes_de": anteriores["itens"][0]["idmensagem"]}
        ).json()
        assert [m["texto"] for m in primeira["itens"]] == ["m1"]
        assert primeira["tem_mais_antigas"] is False

        ultima_vista = recentes["itens"][-1]["idmensagem"]
        assert api.get(url, params={"depois_de": ultima_vista}).json()["itens"] == []
        api.post(url, json={"texto": "m6"})
        novas = api.get(url, params={"depois_de": ultima_vista}).json()["itens"]
        assert [m["texto"] for m in novas] == ["m6"]

    def test_enviar_atualiza_a_ultima_mensagem(self, api, pessoas):
        idconversa = _iniciar(api, pessoas["prestador"]).json()["idconversa"]

        api.post(f"/conversas/{idconversa}/mensagens", json={"texto": "Tchau"})

        assert api.get(f"/conversas/{idconversa}").json()["ultima_mensagem"]["texto"] == "Tchau"
