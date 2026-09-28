from app.models import Cidade


class TestListarCidades:
    def test_lista_cidade_do_piloto(self, api):
        res = api.get("/cidades")

        assert res.status_code == 200
        assert [(c["nome"], c["uf"]) for c in res.json()] == [("Rio Grande", "RS")]

    def test_nao_lista_cidade_inativa(self, api, sessao):
        sessao.add(Cidade(nome="Pelotas", uf="RS", ativo=False))
        sessao.commit()

        nomes = [c["nome"] for c in api.get("/cidades").json()]

        assert "Pelotas" not in nomes
        assert "Rio Grande" in nomes
