from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCriacao(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class Credenciais(BaseModel):
    email: EmailStr
    senha: str


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idusuario: int
    nome: str
    email: EmailStr
    ativo: bool
    criado_em: datetime


# Sem uso no MVP até agora — mantido para avaliação na limpeza de código morto.
class TempoTokenResposta(BaseModel):
    expira_em: datetime
