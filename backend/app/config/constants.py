import os
from pathlib import Path

from dotenv import load_dotenv

# Este módulo é importado antes de qualquer outro que chame load_dotenv (ver main.py);
# sem isto, ENV, CORS_ORIGINS e FRONTEND_URL do .env seriam ignorados.
load_dotenv()

MINUTOS_EXPIRACAO_TOKEN = 60

# Intervalo mínimo entre gravações de usuario.ultimo_acesso_em (evita escrita a cada request).
MINUTOS_ENTRE_REGISTROS_ACESSO = 5

COOKIE_TOKEN_ACESSO = "token_acesso"

# Todo JWT leva a finalidade: um token de redefinição de senha não pode valer como
# sessão, e vice-versa (os dois são assinados com a mesma chave).
FINALIDADE_TOKEN_SESSAO = "sessao"
FINALIDADE_TOKEN_REDEFINIR_SENHA = "redefinir_senha"
MINUTOS_VALIDADE_TOKEN_SENHA = 30

# Base dos links enviados por e-mail (ex.: redefinição de senha).
URL_FRONTEND = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

# Endereço de contato mostrado no rodapé dos e-mails e usado como Reply-To.
EMAIL_SUPORTE = os.getenv("EMAIL_SUPORTE") or None

# Arquivos enviados pelos usuários (fotos, portfólio). Ficam em disco e são servidos
# pela própria API em ROTA_ARQUIVOS; no banco guardamos o caminho público
# ("/arquivos/fotos/<uuid>.jpg"), então dá para trocar por um storage externo depois.
# `or`: UPLOADS_DIR vazio (como no .env.example) também cai no padrão.
DIR_ARQUIVOS = Path(
    os.getenv("UPLOADS_DIR") or Path(__file__).resolve().parents[2] / "arquivos"
).resolve()
ROTA_ARQUIVOS = "/arquivos"
TAMANHO_MAXIMO_IMAGEM_MB = 5

AMBIENTE = os.getenv("ENV", "development").lower()
EM_PRODUCAO = AMBIENTE == "production"

ORIGENS_CORS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]
