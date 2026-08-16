import json
import os

import bcrypt
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from jose import jwt

load_dotenv()

SECRET_KEY = os.getenv("TOKEN_SECRET_KEY")
ALGORITHM = os.getenv("TOKEN_ALGORITHM")

# Chave de encriptação reversível (Fernet)
FERNET = Fernet(os.getenv("ENCRYPTION_KEY", "").encode())


# bcrypt trabalha só com os 72 primeiros bytes da senha; truncar aqui evita
# ValueError em senhas maiores e mantém compat com o hash de verificação.
def _preparar_senha(senha: str) -> bytes:
    return senha.encode("utf-8")[:72]


# Gera o hash da senha
def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(_preparar_senha(senha), bcrypt.gensalt()).decode()


# Compara a senha com um hash
def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(_preparar_senha(senha_plana), senha_hash.encode())


# Gera um salt aleatório de tamanho especifico (padrão: 16)
def gerar_salt(tamanho=16):
    salt = os.urandom(tamanho)
    return salt.hex()


# Cria um token encriptando os dados recebidos
def criar_token(dados: dict):
    payload_limpo = json.loads(json.dumps(dados, default=str))

    token_jwt = jwt.encode(payload_limpo, SECRET_KEY, algorithm=ALGORITHM)
    return token_jwt


def decrypt_token(token, alg=ALGORITHM):
    if token:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[alg])

        return payload
    return None


# Encripta dados de forma reversível
def encrypt_string(string: str) -> str:
    return FERNET.encrypt(string.encode()).decode()


# Desencripta dados
def decrypt_string(string: str) -> str:
    return FERNET.decrypt(string.encode()).decode()
