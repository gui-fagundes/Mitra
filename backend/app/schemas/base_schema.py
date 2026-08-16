from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginBody(BaseModel):
    email: EmailStr
    senha: str


class TempoTokenResponse(BaseModel):
    expira_em: datetime
