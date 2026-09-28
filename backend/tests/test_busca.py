"""Busca de prestadores: visibilidade, filtros, prioridade da cidade, ordenação e paginação."""

from datetime import timedelta
from decimal import Decimal
from itertools import count

import pytest

from app.models import Cidade, PrestadorPerfil, Servico, Usuario
from app.utils.data_utils import agora

_sequencia = count()


@pytest.fixture()
def criar(sessao):
    """Cria um prestador direto no banco. Devolve o idusuario."""
    servicos_por_slug = {s.slug: s for s in sessao.query(Servico).all()}

    def _criar(
        nome="Prestador",
        servicos=("eletroeletronicos",),
        bio=None,
        cidade=None,
        preco_min=None,
        preco_max=None,
        cnpj=None,
        dias_sem_acessar=None,
        ativo=True,
        criado_ha_dias=0,
    ) -> int:
        n = next(_sequencia)
        usuario = Usuario(
            nome=nome,
            email=f"p{n}@test.com",
            senha_hash="x",
            ativo=ativo,
            idcidade=cidade.idcidade if cidade else None,
            ultimo_acesso_em=(
                agora() - timedelta(days=dias_sem_acessar) if dias_sem_acessar is not None else None
            ),
        )
        usuario.prestador_perfil = PrestadorPerfil(
            bio=bio,
            preco_min=Decimal(preco_min) if preco_min is not None else None,
            preco_max=Decimal(preco_max) if preco_max is not None else None,
            cnpj=cnpj,
            criado_em=agora() - timedelta(days=criado_ha_dias),
            servicos=[servicos_por_slug[s] for s in servicos],
        )
        sessao.add(usuario)
        sessao.commit()
        return usuario.idusuario

    return _criar


@pytest.fixture()
def rio_grande(sessao):
    return sessao.query(Cidade).filter_by(nome="Rio Grande").one()


@pytest.fixture()
def pelotas(sessao):
    cidade = Cidade(nome="Pelotas", uf="RS")
    sessao.add(cidade)
    sessao.commit()
    return cidade


def _buscar(api, **params):
    res = api.get("/prestadores", params=params)
    assert res.status_code == 200, res.text
    return res.json()


def _nomes(resultado) -> list[str]:
    return [i["nome"] for i in resultado["itens"]]


class TestVisibilidade:
    def test_publica_sem_login(self, api, criar):
        criar(nome="Ana")

        assert _nomes(_buscar(api)) == ["Ana"]

    def test_prestador_sem_servico_nao_aparece(self, api, criar):
        criar(nome="Com serviço")
        criar(nome="Sem serviço", servicos=())

        assert _nomes(_buscar(api)) == ["Com serviço"]

    def test_conta_inativa_nao_aparece(self, api, criar):
        criar(nome="Ativa")
        criar(nome="Inativa", ativo=False)

        assert _nomes(_buscar(api)) == ["Ativa"]

    def test_servico_inativo_nao_conta(self, api, criar, sessao):
        criar(nome="Só cuidador", servicos=("cuidador",))
        sessao.query(Servico).filter_by(slug="cuidador").one().ativo = False
        sessao.commit()

        assert _buscar(api)["total"] == 0

    def test_card_traz_dados_publicos(self, api, criar, rio_grande):
        criar(
            nome="Bia",
            bio="Eletricista.",
            cidade=rio_grande,
            preco_min=80,
            preco_max=150,
            cnpj="00000000000191",
            servicos=("construcao-manutencao", "eletroeletronicos"),
        )

        card = _buscar(api)["itens"][0]

        assert card["cidade"]["nome"] == "Rio Grande"
        assert card["preco_min"] == 80.0
        assert card["cnpj_validado"] is True
        assert [s["slug"] for s in card["servicos"]] == [
            "eletroeletronicos",
            "construcao-manutencao",
        ]
        assert card["qtd_avaliacoes"] == 0
        assert "cnpj" not in card
        assert "email" not in card


class TestTermo:
    def test_encontra_por_nome_bio_ou_servico(self, api, criar):
        criar(nome="Carlos Silva")
        criar(nome="Outro", bio="Faço instalações elétricas.")
        criar(nome="Terceiro", servicos=("adestramento",))
        criar(nome="Não bate")

        assert _nomes(_buscar(api, termo="silva")) == ["Carlos Silva"]
        assert _nomes(_buscar(api, termo="INSTALAÇÕES")) == ["Outro"]
        assert _nomes(_buscar(api, termo="adestra")) == ["Terceiro"]

    def test_normaliza_espacos(self, api, criar):
        criar(nome="Carlos Silva")

        assert _nomes(_buscar(api, termo="  carlos   silva ")) == ["Carlos Silva"]

    def test_curingas_sao_literais(self, api, criar):
        criar(nome="Ana")

        assert _buscar(api, termo="%")["total"] == 0
        assert _buscar(api, termo="_")["total"] == 0


class TestFiltros:
    def test_categoria(self, api, criar):
        criar(nome="Pets", servicos=("cuidador",))
        criar(nome="Conserto", servicos=("moveis",))

        assert _nomes(_buscar(api, categoria="pets")) == ["Pets"]
        assert _buscar(api, categoria="nao-existe")["total"] == 0

    def test_servicos_atende_qualquer_um_da_lista(self, api, criar, sessao):
        ids = {s.slug: s.idservico for s in sessao.query(Servico).all()}
        criar(nome="Cuidador", servicos=("cuidador",))
        criar(nome="Hospedagem", servicos=("hospedagem",))
        criar(nome="Decoração", servicos=("decoracao",))

        resultado = _buscar(api, servicos=[ids["cuidador"], ids["hospedagem"]])

        assert sorted(_nomes(resultado)) == ["Cuidador", "Hospedagem"]

    def test_somente_cnpj(self, api, criar):
        criar(nome="Com selo", cnpj="00000000000191")
        criar(nome="Sem selo")

        assert _nomes(_buscar(api, somente_cnpj=True)) == ["Com selo"]

    def test_faixa_de_preco_por_sobreposicao(self, api, criar):
        criar(nome="Barato", preco_min=20, preco_max=50)
        criar(nome="Médio", preco_min=80, preco_max=150)
        criar(nome="Caro", preco_min=300, preco_max=500)
        criar(nome="Sob consulta")

        resultado = _buscar(api, preco_min=100, preco_max=200)

        assert sorted(_nomes(resultado)) == ["Médio", "Sob consulta"]

    def test_so_minimo_ou_so_maximo(self, api, criar):
        criar(nome="Barato", preco_min=20, preco_max=50)
        criar(nome="Caro", preco_min=300)

        assert _nomes(_buscar(api, preco_max=100)) == ["Barato"]
        assert _nomes(_buscar(api, preco_min=100)) == ["Caro"]

    def test_nota_minima_sem_avaliacoes_nao_traz_ninguem(self, api, criar):
        criar(nome="Ana")

        assert _buscar(api, nota_min=4)["total"] == 0
        assert _buscar(api, nota_min=0)["total"] == 1

    def test_parametro_invalido_da_422(self, api):
        assert api.get("/prestadores", params={"ordem": "pago"}).status_code == 422
        assert api.get("/prestadores", params={"limite": 51}).status_code == 422


class TestOrdenacao:
    def test_reputacao_sem_avaliacoes_favorece_quem_esta_ativo(self, api, criar):
        criar(nome="Sumido", dias_sem_acessar=200)
        criar(nome="Ativo hoje", dias_sem_acessar=0)
        criar(nome="Ativo há um mês", dias_sem_acessar=30)
        criar(nome="Nunca acessou")

        nomes = _nomes(_buscar(api))

        assert nomes[:2] == ["Ativo hoje", "Ativo há um mês"]

    def test_cidade_informada_vem_primeiro_sem_excluir_as_outras(
        self, api, criar, rio_grande, pelotas
    ):
        criar(nome="Pelotas ativo", cidade=pelotas, dias_sem_acessar=0)
        criar(nome="Rio Grande sumido", cidade=rio_grande, dias_sem_acessar=80)

        nomes = _nomes(_buscar(api, idcidade=rio_grande.idcidade))

        assert nomes == ["Rio Grande sumido", "Pelotas ativo"]

    def test_recentes(self, api, criar):
        criar(nome="Antigo", criado_ha_dias=100)
        criar(nome="Novo", criado_ha_dias=1)

        assert _nomes(_buscar(api, ordem="recentes")) == ["Novo", "Antigo"]


class TestPaginacao:
    def test_limite_deslocamento_e_total(self, api, criar):
        for n in range(5):
            criar(nome=f"P{n}", criado_ha_dias=n)

        primeira = _buscar(api, ordem="recentes", limite=2)
        segunda = _buscar(api, ordem="recentes", limite=2, deslocamento=2)
        ultima = _buscar(api, ordem="recentes", limite=2, deslocamento=4)

        assert primeira["total"] == 5
        assert _nomes(primeira) == ["P0", "P1"]
        assert _nomes(segunda) == ["P2", "P3"]
        assert _nomes(ultima) == ["P4"]

    def test_empate_nao_repete_nem_pula_entre_paginas(self, api, criar):
        # Todos com a mesma pontuação: o desempate precisa ser estável.
        for n in range(6):
            criar(nome=f"Igual {n}")

        vistos = []
        for deslocamento in (0, 2, 4):
            vistos += _nomes(_buscar(api, limite=2, deslocamento=deslocamento))

        assert sorted(vistos) == sorted(f"Igual {n}" for n in range(6))
