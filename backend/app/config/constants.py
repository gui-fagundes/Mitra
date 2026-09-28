import os

from dotenv import load_dotenv

# Este módulo é importado antes de qualquer outro que chame load_dotenv (ver main.py);
# sem isto, ENV e CORS_ORIGINS do .env seriam ignorados.
load_dotenv()

MINUTOS_EXPIRACAO_TOKEN = 60

# Intervalo mínimo entre gravações de usuario.ultimo_acesso_em (evita escrita a cada request).
MINUTOS_ENTRE_REGISTROS_ACESSO = 5

COOKIE_TOKEN_ACESSO = "token_acesso"

AMBIENTE = os.getenv("ENV", "development").lower()
EM_PRODUCAO = AMBIENTE == "production"

ORIGENS_CORS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]
