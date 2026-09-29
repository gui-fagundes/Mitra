"""Export LGPD (RF-DP-02): dados do titular completos, conteúdo de terceiros de fora."""

import pytest

from app.models import Servico

SENHA = "senha1234"
CLIENTE = "cris@test.com"
PRESTADOR = "pedro@test.com"
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def _cadastrar(api, email, nome, papel="cliente"):
    api.post("/conta/sair")
    return api.post(
        "/conta/cadastro",
        json={"nome": nome, "email": email, "senha": SENHA, "aceite_termos": True, "papel": papel},
    ).json()


def _como(api, email):
    api.post("/conta/sair")
    api.cookies.clear()
    api.post("/conta/entrar", json={"email": email, "senha": SENHA})


@pytest.fixture()
def historico(api, sessao):
    """Cris (cliente) e Pedro Alves (prestador): conversa nos dois sentidos, serviço
    concluído, avaliado e respondido, foto e portfólio do Pedro. Termina como Cris."""
    idservico = sessao.query(Servico).filter_by(slug="eletroeletronicos").one().idservico
    pedro = _cadastrar(api, PRESTADOR, "Pedro Alves", "prestador")
    api.put("/conta/foto", files={"arquivo": ("f.jpg", JPEG, "image/jpeg")})
    api.post("/conta/vitrine/portfolio", files={"arquivo": ("p.jpg", JPEG, "image/jpeg")})
    _cadastrar(api, "tina@test.com", "Tina")  # terceira, sem relação
    _cadastrar(api, CLIENTE, "Cris Souza")

    conversa = api.post(
        "/conversas", json={"idprestador": pedro["idusuario"], "texto": "Oi Pedro, segredo da Cris"}
    ).json()["idconversa"]
    idc = api.post(
        f"/conversas/{conversa}/contratacoes",
        json={"idservico": idservico, "descricao": "Trocar tomadas", "valor_estimado": 200},
    ).json()["idcontratacao"]

    _como(api, PRESTADOR)
    api.post(f"/conversas/{conversa}/mensagens", json={"texto": "Oi Cris, segredo do Pedro"})
    api.post(f"/contratacoes/{idc}/aceitar")
    api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 240})

    _como(api, CLIENTE)
    api.post(f"/contratacoes/{idc}/concluir", json={})
    idavaliacao = api.post(
        f"/contratacoes/{idc}/avaliacao", json={"nota": 5, "comentario": "Ótimo"}
    ).json()["idavaliacao"]

    _como(api, PRESTADOR)
    api.post(f"/avaliacoes/{idavaliacao}/resposta", json={"texto": "Obrigado, resposta do Pedro"})
    _como(api, CLIENTE)


def _exportar(api):
    res = api.get("/conta/exportar")
    assert res.status_code == 200
    return res


class TestExportacao:
    def test_download_json(self, api, historico):
        res = _exportar(api)

        assert res.headers["content-type"].startswith("application/json")
        assert 'attachment; filename="mitra-meus-dados-' in res.headers["content-disposition"]

    def test_dados_da_conta_sem_senha(self, api, historico):
        dados = _exportar(api).json()

        assert dados["conta"]["email"] == CLIENTE
        assert dados["conta"]["aceite_termos_em"]
        assert "senha_hash" not in str(dados)
        assert dados["perfil_prestador"] is None
        assert dados["sobre"]

    def test_mensagens_recebidas_vao_sem_conteudo(self, api, historico):
        mensagens = _exportar(api).json()["conversas"][0]["mensagens"]

        textos = [m.get("texto") for m in mensagens]
        assert "Oi Pedro, segredo da Cris" in textos
        assert "Oi Cris, segredo do Pedro" not in textos
        recebida = next(m for m in mensagens if m.get("de") == "outra parte")
        assert recebida["texto"] is None
        assert recebida["enviada_em"]
        # eventos automáticos do sistema vão com texto
        assert any(m.get("tipo") == "evento" and "propôs" in m["texto"] for m in mensagens)

    def test_contratacoes_e_avaliacao_feita(self, api, historico):
        dados = _exportar(api).json()

        contratacao = dados["contratacoes"][0]
        assert contratacao["seu_papel"] == "cliente"
        assert contratacao["com"] == "Pedro Alves"
        assert contratacao["valor_final"] == 240.0
        feita = dados["avaliacoes_feitas"][0]
        assert feita["nota"] == 5
        assert feita["respondida_em"] is not None
        # a resposta foi escrita pelo prestador: o texto não vem
        assert "resposta do Pedro" not in str(dados)
        assert dados["avaliacoes_recebidas"] == []

    def test_prestador_recebe_vitrine_links_e_avaliacoes_recebidas(self, api, historico):
        _como(api, PRESTADOR)

        dados = _exportar(api).json()

        assert dados["conta"]["foto_url"].startswith("http://testserver/arquivos/fotos/")
        perfil = dados["perfil_prestador"]
        assert perfil["portfolio"][0]["imagem_url"].startswith(
            "http://testserver/arquivos/portfolio/"
        )
        recebida = dados["avaliacoes_recebidas"][0]
        assert recebida["autor"] == "Cris S."
        assert recebida["comentario"] == "Ótimo"
        assert recebida["sua_resposta"] == "Obrigado, resposta do Pedro"
        assert "segredo da Cris" not in str(dados)

    def test_nada_de_terceiros_sem_relacao(self, api, historico):
        _como(api, "tina@test.com")

        dados = _exportar(api).json()

        assert dados["conversas"] == []
        assert dados["contratacoes"] == []
        assert dados["avaliacoes_feitas"] == dados["avaliacoes_recebidas"] == []

    def test_sem_login_da_401(self, api):
        assert api.get("/conta/exportar").status_code == 401
