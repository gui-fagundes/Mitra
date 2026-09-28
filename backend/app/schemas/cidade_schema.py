from pydantic import BaseModel, ConfigDict


class CidadeResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idcidade: int
    nome: str
    uf: str
