import json
import os

import bcrypt
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from jose import jwt

load_dotenv()

CHAVE_SECRETA = os.getenv("TOKEN_SECRET_KEY")
ALGORITMO = os.getenv("TOKEN_ALGORITHM")

# Chave de criptografia reversível (Fernet)
FERNET = Fernet(os.getenv("ENCRYPTION_KEY", "").encode())


# bcrypt trabalha só com os 72 primeiros bytes da senha; truncar aqui evita
# ValueError em senhas maiores e mantém compat com o hash de verificação.
def _preparar_senha(senha: str) -> bytes:
    return senha.encode("utf-8")[:72]


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(_preparar_senha(senha), bcrypt.gensalt()).decode()


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(_preparar_senha(senha_plana), senha_hash.encode())


def criar_token(dados: dict) -> str:
    """Assina os dados como JWT."""
    payload = json.loads(json.dumps(dados, default=str))
    return jwt.encode(payload, CHAVE_SECRETA, algorithm=ALGORITMO)


def decodificar_token(token: str | None) -> dict | None:
    """Valida assinatura e expiração do JWT. Levanta JWTError se inválido."""
    if not token:
        return None
    return jwt.decode(token, CHAVE_SECRETA, algorithms=[ALGORITMO])


# Daqui para baixo: sem uso no MVP até agora — mantido para avaliação na limpeza
# de código morto (ver docs/backend-plan.md, "Limpeza de código sem uso").


def gerar_salt(tamanho: int = 16) -> str:
    """Gera um salt aleatório em hex. (O bcrypt já gera o próprio salt.)"""
    return os.urandom(tamanho).hex()


def criptografar_texto(texto: str) -> str:
    """Criptografa de forma reversível (Fernet)."""
    return FERNET.encrypt(texto.encode()).decode()


def descriptografar_texto(texto: str) -> str:
    return FERNET.decrypt(texto.encode()).decode()
