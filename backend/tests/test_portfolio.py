"""Portfólio do prestador: upload, legenda, reordenação, remoção e limite de 10."""

import pytest

from app.config.constants import DIR_ARQUIVOS, ROTA_ARQUIVOS
from app.services.portfolio_services import LIMITE_PORTFOLIO

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64

URL = "/conta/vitrine/portfolio"


def _no_disco(caminho_publico: str):
    return DIR_ARQUIVOS / caminho_publico.removeprefix(f"{ROTA_ARQUIVOS}/")


def _cadastrar(api, papel="prestador", email="lia@test.com"):
    return api.post(
        "/conta/cadastro",
        json={
            "nome": "Lia",
            "email": email,
            "senha": "senha1234",
            "aceite_termos": True,
            "papel": papel,
        },
    ).json()


def _enviar(api, conteudo=JPEG, legenda=None):
    dados = {"legenda": legenda} if legenda is not None else None
    return api.post(URL, files={"arquivo": ("obra.jpg", conteudo, "image/jpeg")}, data=dados)


@pytest.fixture()
def prestador(api):
    return _cadastrar(api)


class TestAdicionar:
    def test_adiciona_com_legenda(self, api, prestador):
        res = _enviar(api, legenda="  Instalação na cozinha  ")

        assert res.status_code == 201
        item = res.json()
        assert item["legenda"] == "Instalação na cozinha"
        assert item["ordem"] == 0
        assert item["imagem_url"].startswith(f"{ROTA_ARQUIVOS}/portfolio/")
        assert _no_disco(item["imagem_url"]).exists()

    def test_novas_imagens_entram_no_fim(self, api, prestador):
        ordens = [_enviar(api).json()["ordem"] for _ in range(3)]

        assert ordens == [0, 1, 2]

    def test_aparece_na_vitrine_e_no_perfil_publico(self, api, prestador):
        _enviar(api, legenda="Antes")
        _enviar(api, PNG, legenda="Depois")

        vitrine = api.get("/conta/vitrine").json()
        publico = api.get(f"/prestadores/{prestador['idusuario']}").json()

        assert [i["legenda"] for i in vitrine["portfolio"]] == ["Antes", "Depois"]
        assert [i["legenda"] for i in publico["portfolio"]] == ["Antes", "Depois"]

    def test_limite_de_imagens(self, api, prestador):
        for _ in range(LIMITE_PORTFOLIO):
            assert _enviar(api).status_code == 201
        antes = len(list((DIR_ARQUIVOS / "portfolio").iterdir()))

        res = _enviar(api)

        assert res.status_code == 422
        # recusou antes de gravar o arquivo
        assert len(list((DIR_ARQUIVOS / "portfolio").iterdir())) == antes

    def test_recusa_arquivo_que_nao_e_imagem(self, api, prestador):
        assert _enviar(api, b"nao sou imagem").status_code == 415

    def test_legenda_longa_demais_da_422(self, api, prestador):
        assert _enviar(api, legenda="x" * 256).status_code == 422

    def test_cliente_sem_vitrine_recebe_404(self, api):
        _cadastrar(api, papel="cliente")

        assert _enviar(api).status_code == 404


class TestEditarLegenda:
    def test_edita_e_limpa_legenda(self, api, prestador):
        item = _enviar(api, legenda="Antiga").json()
        url = f"{URL}/{item['idprestadorportfolio']}"

        assert api.patch(url, json={"legenda": "Nova"}).json()["legenda"] == "Nova"
        assert api.patch(url, json={"legenda": "   "}).json()["legenda"] is None

    def test_item_de_outro_prestador_da_404(self, api, prestador):
        alheio = _enviar(api).json()["idprestadorportfolio"]
        api.post("/conta/sair")
        _cadastrar(api, email="outro@test.com")

        res = api.patch(f"{URL}/{alheio}", json={"legenda": "invasão"})

        assert res.status_code == 404


class TestRemover:
    def test_remove_do_banco_e_do_disco_e_renumera(self, api, prestador):
        itens = [_enviar(api, legenda=str(n)).json() for n in range(3)]

        res = api.delete(f"{URL}/{itens[0]['idprestadorportfolio']}")

        assert res.status_code == 204
        assert not _no_disco(itens[0]["imagem_url"]).exists()
        restantes = api.get("/conta/vitrine").json()["portfolio"]
        assert [(i["legenda"], i["ordem"]) for i in restantes] == [("1", 0), ("2", 1)]

    def test_item_de_outro_prestador_nao_e_removido(self, api, prestador):
        alheio = _enviar(api).json()
        api.post("/conta/sair")
        _cadastrar(api, email="outro@test.com")

        assert api.delete(f"{URL}/{alheio['idprestadorportfolio']}").status_code == 404
        assert _no_disco(alheio["imagem_url"]).exists()


class TestReordenar:
    def test_aplica_a_nova_ordem(self, api, prestador):
        ids = [_enviar(api, legenda=str(n)).json()["idprestadorportfolio"] for n in range(3)]

        res = api.put(f"{URL}/ordem", json={"ids": [ids[2], ids[0], ids[1]]})

        assert res.status_code == 200
        assert [i["legenda"] for i in res.json()] == ["2", "0", "1"]
        assert [i["legenda"] for i in api.get("/conta/vitrine").json()["portfolio"]] == [
            "2",
            "0",
            "1",
        ]

    @pytest.mark.parametrize(
        "montar",
        [
            lambda ids: ids[:2],  # faltando um
            lambda ids: [*ids, ids[0]],  # repetido
            lambda ids: [*ids[:2], 999999],  # id estranho
        ],
    )
    def test_lista_incompleta_ou_estranha_da_422(self, api, prestador, montar):
        ids = [_enviar(api).json()["idprestadorportfolio"] for _ in range(3)]

        assert api.put(f"{URL}/ordem", json={"ids": montar(ids)}).status_code == 422
