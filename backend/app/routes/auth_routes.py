from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.config.dependencies import get_current_user, get_db
from app.models.usuario_model import Usuario
from app.schemas.base_schema import LoginBody
from app.schemas.usuario_schema import UsuarioCreate, UsuarioResponse
from app.services import auth_services
from app.utils.cookie_utils import clear_auth_cookie, set_auth_cookie

auth_router = APIRouter(prefix="/auth", tags=["Autenticação"])


@auth_router.post("/signup", response_model=UsuarioResponse)
def signup(body: UsuarioCreate, response: Response, db: Session = Depends(get_db)):
    usuario = auth_services.signup(body.model_dump(), db)
    set_auth_cookie(response, auth_services.gerar_token(usuario))
    return usuario


@auth_router.post("/login", response_model=UsuarioResponse)
def login(body: LoginBody, response: Response, db: Session = Depends(get_db)):
    usuario = auth_services.login(body.model_dump(), db)
    set_auth_cookie(response, auth_services.gerar_token(usuario))
    return usuario


@auth_router.post("/logout", status_code=204)
def logout(response: Response):
    clear_auth_cookie(response)


@auth_router.get("/me", response_model=UsuarioResponse)
def me(current_user: Usuario = Depends(get_current_user)):
    return current_user
