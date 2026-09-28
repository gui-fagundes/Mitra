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

    mensagem = EmailMessage()
    mensagem["From"] = os.getenv("SMTP_FROM", "Mitra <nao-responda@mitra.local>")
    mensagem["To"] = para
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo_texto)
    if corpo_html:
        mensagem.add_alternative(corpo_html, subtype="html")

    porta = int(os.getenv("SMTP_PORT", "587"))
    try:
        await aiosmtplib.send(
            mensagem,
            hostname=host,
            port=porta,
            username=os.getenv("SMTP_USER") or None,
            password=os.getenv("SMTP_PASSWORD") or None,
            # 465 = TLS direto; nas outras portas o aiosmtplib faz STARTTLS se o servidor oferecer.
            use_tls=porta == 465,
            timeout=15,
        )
    except Exception as e:
        print(f"Falha ao enviar e-mail para {para}: {e!r}", flush=True)
