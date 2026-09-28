from app.models import Categoria, Servico


class TestListarCategorias:
    def test_retorna_as_5_categorias_em_ordem_com_servicos(self, api):
        res = api.get("/categorias")

        assert res.status_code == 200
        categorias = res.json()
        assert [c["slug"] for c in categorias] == [
            "conserto",
            "educacao",
            "pets",
            "entretenimento",
            "artesanato",
        ]
        assert [len(c["servicos"]) for c in categorias] == [4, 3, 4, 3, 3]
        assert categorias[0]["icone"] == "fa-wrench"
        assert [s["nome"] for s in categorias[2]["servicos"]] == [
            "Adestramento",
            "Banho / tosa",
            "Cuidador",
            "Hospedagem",
        ]

    def test_publico_sem_autenticacao(self, api):
        assert api.get("/categorias").status_code == 200

    def test_nao_lista_servico_inativo(self, api, sessao):
        sessao.query(Servico).filter_by(slug="cuidador").one().ativo = False
        sessao.commit()

        pets = next(c for c in api.get("/categorias").json() if c["slug"] == "pets")

        assert "Cuidador" not in [s["nome"] for s in pets["servicos"]]

    def test_nao_lista_categoria_inativa(self, api, sessao):
        sessao.query(Categoria).filter_by(slug="pets").one().ativo = False
        sessao.commit()

        slugs = [c["slug"] for c in api.get("/categorias").json()]

        assert "pets" not in slugs


class TestListarServicos:
    def test_sem_filtro_retorna_todos(self, api):
        res = api.get("/servicos")

        assert res.status_code == 200
        assert len(res.json()) == 17

    def test_filtra_por_categoria(self, api):
        res = api.get("/servicos", params={"categoria": "educacao"})

        assert [s["slug"] for s in res.json()] == [
            "aulas-particulares",
            "personal-trainer",
            "treinamentos",
        ]

    def test_categoria_inexistente_da_404(self, api):
        res = api.get("/servicos", params={"categoria": "nao-existe"})

        assert res.status_code == 404

    def test_nao_lista_servico_de_categoria_inativa(self, api, sessao):
        sessao.query(Categoria).filter_by(slug="pets").one().ativo = False
        sessao.commit()

        assert len(api.get("/servicos").json()) == 13
        assert api.get("/servicos", params={"categoria": "pets"}).status_code == 404
