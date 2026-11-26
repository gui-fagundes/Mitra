import os
from email.message import EmailMessage

import aiosmtplib


async def enviar_email(
    para: str, assunto: str, corpo_texto: str, corpo_html: str | None = None
) -> None:
    """Envia um e-mail via SMTP. Feita para rodar em BackgroundTasks: nunca levanta.

    Sem SMTP_HOST configurado (desenvolvimento e testes), só imprime o e-mail no log.
    A configuração é lida a cada envio, então mudanças no ambiente valem sem reiniciar.
    """
    host = os.getenv("SMTP_HOST")
    if not host:
        print(
            f"[e-mail não enviado: SMTP_HOST vazio] Para: {para} | {assunto}\n{corpo_texto}",
            flush=True,
        )
        return

    usuario_smtp = os.getenv("SMTP_USER") or None
    mensagem = EmailMessage()
    # O Gmail (e a maioria dos provedores) só aceita como remetente a própria conta.
    mensagem["From"] = (
        os.getenv("SMTP_FROM")
        or (f"Mitra <{usuario_smtp}>" if usuario_smtp else None)
        or "Mitra <nao-responda@mitra.local>"
    )
    mensagem["To"] = para
    mensagem["Subject"] = assunto
    if suporte := os.getenv("EMAIL_SUPORTE"):
        mensagem["Reply-To"] = suporte
    mensagem.set_content(corpo_texto)
    if corpo_html:
        mensagem.add_alternative(corpo_html, subtype="html")

    porta = int(os.getenv("SMTP_PORT", "587"))
    try:
        await aiosmtplib.send(
            mensagem,
            hostname=host,
            port=porta,
            username=usuario_smtp,
            password=os.getenv("SMTP_PASSWORD") or None,
            # 465 = TLS direto; nas outras portas o aiosmtplib faz STARTTLS se o servidor oferecer.
            use_tls=porta == 465,
            timeout=15,
        )
    except Exception as e:
        print(f"Falha ao enviar e-mail para {para}: {e!r}", flush=True)
