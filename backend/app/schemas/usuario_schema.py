from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.cidade_schema import CidadeResposta


class UsuarioCriacao(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    idcidade: int | None = None
    telefone: str | None = Field(default=None, max_length=32)
    # RF-DP-01: obrigatório e precisa ser true.
    aceite_termos: bool
    # Todo usuário pode contratar; "prestador" e "ambos" já criam a vitrine (vazia).
    papel: Literal["cliente", "prestador", "ambos"] = "cliente"

    @field_validator("aceite_termos")
    @classmethod
    def exigir_aceite(cls, valor: bool) -> bool:
        if not valor:
            raise ValueError("É preciso aceitar os Termos de Uso e a Política de Privacidade")
        return valor


class UsuarioAtualizacao(BaseModel):
    """Campos ausentes não mudam. `null` limpa os opcionais (cidade, telefone).

    A foto não entra aqui: só muda por upload (PUT/DELETE /conta/foto).
    """

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    idcidade: int | None = None
    telefone: str | None = Field(default=None, max_length=32)
    notificar_email: bool | None = None
    busca_somente_cnpj: bool | None = None

    @model_validator(mode="after")
    def proibir_nulo_nos_obrigatorios(self):
        for campo in ("nome", "notificar_email", "busca_somente_cnpj"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"'{campo}' não pode ser nulo")
        return self


class Credenciais(BaseModel):
    email: EmailStr
    senha: str


class EsqueciSenhaEntrada(BaseModel):
    email: EmailStr


class RedefinirSenhaEntrada(BaseModel):
    token: str
    nova_senha: str = Field(min_length=8, max_length=128)


class VerificarEmailEntrada(BaseModel):
    token: str


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idusuario: int
    nome: str
    email: EmailStr
    telefone: str | None
    foto_url: str | None
    cidade: CidadeResposta | None
    aceite_termos_em: datetime | None
    email_verificado_em: datetime | None
    notificar_email: bool
    busca_somente_cnpj: bool
    e_prestador: bool
    ativo: bool
    criado_em: datetime


# Sem uso no MVP até agora — mantido para avaliação na limpeza de código morto.
class TempoTokenResposta(BaseModel):
    expira_em: datetime
