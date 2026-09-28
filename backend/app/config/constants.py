import os

MINUTOS_EXPIRACAO_TOKEN = 60

COOKIE_TOKEN_ACESSO = "token_acesso"

AMBIENTE = os.getenv("ENV", "development").lower()
EM_PRODUCAO = AMBIENTE == "production"

ORIGENS_CORS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]
