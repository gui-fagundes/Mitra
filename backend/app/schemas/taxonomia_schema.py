from pydantic import BaseModel, ConfigDict, Field


class ServicoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idservico: int
    idcategoria: int
    nome: str
    slug: str


class CategoriaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idcategoria: int
    nome: str
    slug: str
    icone: str
    servicos: list[ServicoResposta] = Field(validation_alias="servicos_ativos")
