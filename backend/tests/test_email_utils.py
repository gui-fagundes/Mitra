import asyncio

from app.utils import email_utils


def _enviar():
    asyncio.run(email_utils.enviar_email("ana@test.com", "Assunto", "Corpo do e-mail"))


class TestEnviarEmail:
    def test_sem_smtp_configurado_so_registra_no_log(self, monkeypatch, capsys):
        monkeypatch.delenv("SMTP_HOST", raising=False)
        chamadas = []
        monkeypatch.setattr(email_utils.aiosmtplib, "send", lambda *a, **k: chamadas.append(a))

        _enviar()

        assert chamadas == []
        assert "ana@test.com" in capsys.readouterr().out

    def test_com_smtp_envia_a_mensagem(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.exemplo.com")
        monkeypatch.setenv("SMTP_PORT", "465")
        monkeypatch.setenv("SMTP_FROM", "Mitra <nao-responda@exemplo.com>")
        enviados = []

        async def _send(mensagem, **opcoes):
            enviados.append((mensagem, opcoes))

        monkeypatch.setattr(email_utils.aiosmtplib, "send", _send)

        _enviar()

        mensagem, opcoes = enviados[0]
        assert mensagem["To"] == "ana@test.com"
        assert mensagem["Subject"] == "Assunto"
        assert mensagem["From"] == "Mitra <nao-responda@exemplo.com>"
        assert "Corpo do e-mail" in mensagem.get_content()
        assert opcoes["hostname"] == "smtp.exemplo.com"
        assert opcoes["use_tls"] is True

    def test_falha_no_smtp_nao_propaga(self, monkeypatch, capsys):
        monkeypatch.setenv("SMTP_HOST", "smtp.exemplo.com")

        async def _falhar(*_a, **_k):
            raise ConnectionRefusedError("servidor fora do ar")

        monkeypatch.setattr(email_utils.aiosmtplib, "send", _falhar)

        _enviar()  # não levanta

        assert "Falha ao enviar e-mail" in capsys.readouterr().out

    def test_sem_smtp_from_usa_a_conta_smtp_e_reply_to_do_suporte(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.exemplo.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.delenv("SMTP_FROM", raising=False)
        monkeypatch.setenv("SMTP_USER", "conta@exemplo.com")
        monkeypatch.setenv("EMAIL_SUPORTE", "suporte@exemplo.com")
        enviados = []

        async def _send(mensagem, **opcoes):
            enviados.append((mensagem, opcoes))

        monkeypatch.setattr(email_utils.aiosmtplib, "send", _send)

        _enviar()

        mensagem, opcoes = enviados[0]
        assert mensagem["From"] == "Mitra <conta@exemplo.com>"
        assert mensagem["Reply-To"] == "suporte@exemplo.com"
        assert opcoes["use_tls"] is False
