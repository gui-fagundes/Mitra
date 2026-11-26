"""Avisos por e-mail em eventos-chave (RF-CO-03)."""

from datetime import timedelta

import pytest

from app.models import Mensagem, Servico, Usuario
from app.utils.data_utils import agora

SENHA = "senha1234"
CLIENTE = "cris@test.com"
PRESTADOR = "pedro@test.com"


def _cadastrar(api, sessao, email, nome, papel="cliente", verificar=True):
    api.post("/conta/sair")
    conta = api.post(
        "/conta/cadastro",
        json={"nome": nome, "email": email, "senha": SENHA, "aceite_termos": True, "papel": papel},
    ).json()
    if verificar:
        usuario = sessao.get(Usuario, conta["idusuario"])
        usuario.email_verificado_em = agora()
        sessao.commit()
    return conta


def _como(api, email):
    api.post("/conta/sair")
    api.cookies.clear()
    api.post("/conta/entrar", json={"email": email, "senha": SENHA})


def _envelhecer_mensagens(sessao, idconversa, horas=1):
    for m in sessao.query(Mensagem).filter_by(idconversa=idconversa):
        m.criado_em -= timedelta(hours=horas)
    sessao.commit()


@pytest.fixture()
def partes(api, sessao, emails):
    """Pedro (prestador) e Cris (cliente), ambos com e-mail confirmado. Termina como Cris,
    com a lista de e-mails já sem os de confirmação de cadastro."""
    pedro = _cadastrar(api, sessao, PRESTADOR, "Pedro Alves", "prestador")
    cris = _cadastrar(api, sessao, CLIENTE, "Cris Souza")
    emails.clear()
    return pedro, cris


def _iniciar(api, pedro, texto="Oi Pedro, preciso trocar tomadas"):
    return api.post("/conversas", json={"idprestador": pedro["idusuario"], "texto": texto}).json()[
        "idconversa"
    ]


class TestContatoEMensagens:
    def test_primeiro_contato_avisa_o_prestador(self, api, emails, partes):
        pedro, _ = partes

        idconversa = _iniciar(api, pedro)

        assert len(emails) == 1
        aviso = emails[0]
        assert aviso["para"] == PRESTADOR
        assert aviso["assunto"] == "Cris Souza entrou em contato pelo Mitra"
        assert "preciso trocar tomadas" in aviso["corpo"]
        assert f"/mensagens/{idconversa}" in aviso["corpo"]

    def test_sequencia_do_mesmo_autor_nao_repete_aviso(self, api, emails, partes):
        pedro, _ = partes
        idconversa = _iniciar(api, pedro)

        api.post(f"/conversas/{idconversa}/mensagens", json={"texto": "É no Cassino"})

        assert len(emails) == 1

    def test_resposta_durante_a_conversa_nao_avisa(self, api, emails, partes):
        pedro, _ = partes
        idconversa = _iniciar(api, pedro)
        _como(api, PRESTADOR)

        api.post(f"/conversas/{idconversa}/mensagens", json={"texto": "Atendo sim"})

        # Cris escreveu há instantes: está na conversa, não precisa de e-mail.
        assert len(emails) == 1

    def test_mensagem_nova_depois_de_um_tempo_avisa(self, api, sessao, emails, partes):
        pedro, _ = partes
        idconversa = _iniciar(api, pedro)
        _envelhecer_mensagens(sessao, idconversa)
        _como(api, PRESTADOR)

        api.post(f"/conversas/{idconversa}/mensagens", json={"texto": "Posso ir amanhã"})

        aviso = emails[-1]
        assert aviso["para"] == CLIENTE
        assert aviso["assunto"] == "Nova mensagem de Pedro Alves · Mitra"
        assert "Posso ir amanhã" in aviso["corpo"]

    def test_quem_desligou_os_avisos_nao_recebe(self, api, sessao, emails, partes):
        pedro, _ = partes
        sessao.get(Usuario, pedro["idusuario"]).notificar_email = False
        sessao.commit()

        _iniciar(api, pedro)

        assert emails == []

    def test_email_nao_confirmado_nao_recebe(self, api, sessao, emails):
        pedro = _cadastrar(api, sessao, PRESTADOR, "Pedro Alves", "prestador", verificar=False)
        _cadastrar(api, sessao, CLIENTE, "Cris Souza")
        emails.clear()

        _iniciar(api, pedro)

        assert emails == []

    def test_trecho_longo_e_cortado(self, api, emails, partes):
        pedro, _ = partes

        _iniciar(api, pedro, texto="a" * 1000)

        assert "a" * 400 not in emails[0]["corpo"]
        assert "…" in emails[0]["corpo"]


class TestContratacaoEAvaliacao:
    def test_proposta_avisa_a_outra_parte(self, api, sessao, emails, partes):
        pedro, _ = partes
        idconversa = _iniciar(api, pedro)
        emails.clear()
        idservico = sessao.query(Servico).filter_by(slug="eletroeletronicos").one().idservico

        idc = api.post(
            f"/conversas/{idconversa}/contratacoes",
            json={"idservico": idservico, "descricao": "Trocar tomadas", "valor_estimado": 200},
        ).json()["idcontratacao"]

        assert len(emails) == 1
        assert emails[0]["para"] == PRESTADOR
        assert emails[0]["assunto"] == "Novidade na contratação com Cris Souza · Mitra"
        assert "propôs um serviço" in emails[0]["corpo"]
        assert f"/servico/{idc}/confirmar" in emails[0]["corpo"]

    def test_ciclo_completo_e_avaliacao(self, api, sessao, emails, partes):
        pedro, _ = partes
        idconversa = _iniciar(api, pedro)
        idservico = sessao.query(Servico).filter_by(slug="eletroeletronicos").one().idservico
        idc = api.post(
            f"/conversas/{idconversa}/contratacoes",
            json={"idservico": idservico, "descricao": "Trocar tomadas", "valor_estimado": 200},
        ).json()["idcontratacao"]
        _como(api, PRESTADOR)
        api.post(f"/contratacoes/{idc}/aceitar")
        api.post(f"/contratacoes/{idc}/concluir", json={"valor_final": 240})
        _como(api, CLIENTE)
        emails.clear()

        api.post(f"/contratacoes/{idc}/concluir", json={})
        assert emails[-1]["para"] == PRESTADOR
        assert "Serviço concluído" in emails[-1]["corpo"]

        idavaliacao = api.post(
            f"/contratacoes/{idc}/avaliacao", json={"nota": 5, "comentario": "Ótimo"}
        ).json()["idavaliacao"]
        assert emails[-1]["para"] == PRESTADOR
        assert emails[-1]["assunto"] == "Você recebeu uma avaliação no Mitra"

        _como(api, PRESTADOR)
        api.post(f"/avaliacoes/{idavaliacao}/resposta", json={"texto": "Obrigado!"})
        assert emails[-1]["para"] == CLIENTE
        assert "respondeu à avaliação" in emails[-1]["corpo"]

    def test_quem_age_nunca_recebe_o_proprio_aviso(self, api, sessao, emails, partes):
        pedro, _ = partes
        idconversa = _iniciar(api, pedro)
        idservico = sessao.query(Servico).filter_by(slug="eletroeletronicos").one().idservico
        api.post(
            f"/conversas/{idconversa}/contratacoes",
            json={"idservico": idservico, "descricao": "Trocar tomadas"},
        )

        assert all(e["para"] == PRESTADOR for e in emails)
