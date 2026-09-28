"""Perfil do prestador: papel no cadastro, vitrine do próprio usuário e perfil público."""

import pytest

from app.models import Cidade, Servico, Usuario


def _cadastrar(api, papel="cliente", email="pri@test.com", **extra):
    return api.post(
        "/conta/cadastro",
        json={
            "nome": "Pri",
            "email": email,
            "senha": "senha1234",
            "aceite_termos": True,
            "papel": papel,
            **extra,
        },
    )


def _servicos(sessao, *slugs) -> list[int]:
    por_slug = {s.slug: s.idservico for s in sessao.query(Servico).all()}
    return [por_slug[s] for s in slugs]


@pytest.fixture()
def prestador(api):
    """Usuário logado que se cadastrou como prestador (vitrine vazia)."""
    return _cadastrar(api, papel="prestador").json()


class TestPapelNoCadastro:
    def test_cliente_nao_tem_vitrine(self, api):
        corpo = _cadastrar(api).json()

        assert corpo["e_prestador"] is False
        assert api.get("/conta/vitrine").status_code == 404

    @pytest.mark.parametrize("papel", ["prestador", "ambos"])
    def test_prestador_e_ambos_ja_criam_vitrine_vazia(self, api, papel):
        corpo = _cadastrar(api, papel=papel).json()

        assert corpo["e_prestador"] is True
        vitrine = api.get("/conta/vitrine").json()
        assert vitrine["bio"] is None
        assert vitrine["servicos"] == []
        assert vitrine["cnpj_validado"] is False

    def test_papel_padrao_e_cliente(self, api):
        res = api.post(
            "/conta/cadastro",
            json={"nome": "X", "email": "x@test.com", "senha": "senha1234", "aceite_termos": True},
        )

        assert res.json()["e_prestador"] is False

    def test_papel_invalido_da_422(self, api):
        assert _cadastrar(api, papel="admin").status_code == 422

    def test_obter_conta_informa_e_prestador(self, api, prestador):
        assert api.get("/conta").json()["e_prestador"] is True


class TestCriarVitrine:
    def test_cliente_vira_prestador(self, api, sessao):
        _cadastrar(api)
        ids = _servicos(sessao, "adestramento", "banho-tosa")

        res = api.post(
            "/conta/vitrine",
            json={"bio": " Cuido do seu pet. ", "preco_min": 50, "servicos": ids},
        )

        assert res.status_code == 201
        corpo = res.json()
        assert corpo["bio"] == "Cuido do seu pet."
        assert corpo["preco_min"] == 50.0
        assert [s["slug"] for s in corpo["servicos"]] == ["adestramento", "banho-tosa"]
        assert api.get("/conta").json()["e_prestador"] is True

    def test_quem_ja_tem_vitrine_recebe_409(self, api, prestador):
        assert api.post("/conta/vitrine", json={}).status_code == 409

    def test_sem_login_da_401(self, api):
        assert api.post("/conta/vitrine", json={}).status_code == 401


class TestAtualizarVitrine:
    def test_atualiza_campos_e_servicos(self, api, prestador, sessao):
        ids = _servicos(sessao, "eletroeletronicos", "construcao-manutencao")

        res = api.patch(
            "/conta/vitrine",
            json={
                "bio": "Eletricista há 10 anos.",
                "preco_min": 80,
                "preco_max": 150.5,
                "disponibilidade": "Seg a Sáb · 8h–18h",
                "servicos": ids,
            },
        )

        assert res.status_code == 200
        corpo = res.json()
        assert corpo["preco_max"] == 150.5
        assert corpo["disponibilidade"] == "Seg a Sáb · 8h–18h"
        assert len(corpo["servicos"]) == 2

    def test_campos_ausentes_nao_mudam(self, api, prestador, sessao):
        api.patch(
            "/conta/vitrine",
            json={"bio": "Bio", "servicos": _servicos(sessao, "cuidador")},
        )

        corpo = api.patch("/conta/vitrine", json={"preco_min": 30}).json()

        assert corpo["bio"] == "Bio"
        assert [s["slug"] for s in corpo["servicos"]] == ["cuidador"]

    def test_servicos_substitui_a_lista(self, api, prestador, sessao):
        api.patch("/conta/vitrine", json={"servicos": _servicos(sessao, "cuidador", "hospedagem")})

        corpo = api.patch(
            "/conta/vitrine", json={"servicos": _servicos(sessao, "decoracao")}
        ).json()

        assert [s["slug"] for s in corpo["servicos"]] == ["decoracao"]

    def test_lista_vazia_remove_todos(self, api, prestador, sessao):
        api.patch("/conta/vitrine", json={"servicos": _servicos(sessao, "cuidador")})

        assert api.patch("/conta/vitrine", json={"servicos": []}).json()["servicos"] == []

    def test_quarto_servico_da_422(self, api, prestador, sessao):
        ids = _servicos(sessao, "cuidador", "hospedagem", "adestramento", "banho-tosa")

        assert api.patch("/conta/vitrine", json={"servicos": ids}).status_code == 422

    def test_servico_repetido_da_422(self, api, prestador, sessao):
        (id_,) = _servicos(sessao, "cuidador")

        assert api.patch("/conta/vitrine", json={"servicos": [id_, id_]}).status_code == 422

    def test_servico_inexistente_da_422(self, api, prestador):
        assert api.patch("/conta/vitrine", json={"servicos": [999999]}).status_code == 422

    def test_servico_inativo_da_422(self, api, prestador, sessao):
        servico = sessao.query(Servico).filter_by(slug="cuidador").one()
        servico.ativo = False
        sessao.commit()

        res = api.patch("/conta/vitrine", json={"servicos": [servico.idservico]})

        assert res.status_code == 422

    def test_bio_acima_de_400_caracteres_da_422(self, api, prestador):
        assert api.patch("/conta/vitrine", json={"bio": "x" * 401}).status_code == 422

    def test_preco_negativo_da_422(self, api, prestador):
        assert api.patch("/conta/vitrine", json={"preco_min": -1}).status_code == 422

    def test_minimo_maior_que_maximo_no_mesmo_envio_da_422(self, api, prestador):
        res = api.patch("/conta/vitrine", json={"preco_min": 200, "preco_max": 100})

        assert res.status_code == 422

    def test_minimo_maior_que_maximo_ja_salvo_da_422(self, api, prestador):
        api.patch("/conta/vitrine", json={"preco_max": 100})

        assert api.patch("/conta/vitrine", json={"preco_min": 200}).status_code == 422

    def test_cliente_sem_vitrine_recebe_404(self, api):
        _cadastrar(api)

        assert api.patch("/conta/vitrine", json={"bio": "x"}).status_code == 404


class TestPerfilPublico:
    def test_mostra_dados_publicos(self, api, prestador, sessao):
        cidade = sessao.query(Cidade).filter_by(nome="Rio Grande").one()
        api.patch("/conta", json={"idcidade": cidade.idcidade})
        api.patch(
            "/conta/vitrine",
            json={
                "bio": "Adestradora.",
                "preco_min": 60,
                "servicos": _servicos(sessao, "banho-tosa", "adestramento", "decoracao"),
            },
        )
        api.cookies.clear()  # perfil público não exige login

        res = api.get(f"/prestadores/{prestador['idusuario']}")

        assert res.status_code == 200
        corpo = res.json()
        assert corpo["nome"] == "Pri"
        assert corpo["cidade"]["nome"] == "Rio Grande"
        assert corpo["bio"] == "Adestradora."
        # na ordem da taxonomia, não na ordem de envio
        assert [s["slug"] for s in corpo["servicos"]] == [
            "adestramento",
            "banho-tosa",
            "decoracao",
        ]
        assert [c["slug"] for c in corpo["categorias"]] == ["pets", "artesanato"]
        assert corpo["cnpj_validado"] is False
        assert corpo["prestador_desde"]
        assert corpo["qtd_avaliacoes"] == 0
        assert "email" not in corpo
        assert "telefone" not in corpo

    def test_cliente_nao_tem_perfil_publico(self, api):
        cliente = _cadastrar(api).json()

        assert api.get(f"/prestadores/{cliente['idusuario']}").status_code == 404

    def test_prestador_inativo_some(self, api, prestador, sessao):
        sessao.get(Usuario, prestador["idusuario"]).ativo = False
        sessao.commit()

        assert api.get(f"/prestadores/{prestador['idusuario']}").status_code == 404

    def test_inexistente_da_404(self, api):
        assert api.get("/prestadores/999999").status_code == 404
