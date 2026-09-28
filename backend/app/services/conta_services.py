import hashlib
from datetime import timedelta

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config.constants import (
    FINALIDADE_TOKEN_REDEFINIR_SENHA,
    MINUTOS_VALIDADE_TOKEN_SENHA,
    URL_FRONTEND,
)
from app.models.usuario_model import Usuario
from app.services import usuario_services
from app.utils.data_utils import agora
from app.utils.seguranca_utils import (
    criar_token,
    criar_token_sessao,
    decodificar_token,
    gerar_hash_senha,
    verificar_senha,
)


def gerar_token(usuario: Usuario) -> str:
    return criar_token_sessao(usuario.idusuario)


def entrar(payload: dict, db: Session) -> Usuario:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha inválidos",
    )

    usuario = usuario_services.buscar_por_email(payload["email"], db)
    if not usuario or not verificar_senha(payload["senha"], usuario.senha_hash):
        raise credenciais_invalidas

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    return usuario


def cadastrar(payload: dict, db: Session) -> Usuario:
    return usuario_services.criar_usuario(payload, db)


def atualizar(usuario: Usuario, payload: dict, db: Session) -> Usuario:
    return usuario_services.atualizar_usuario(usuario, payload, db)


# --- Esqueci minha senha -------------------------------------------------------
#
# Token stateless de uso único, sem tabela: o JWT carrega uma impressão do
# senha_hash atual. Quando a senha muda, o hash muda e todo token emitido antes
# (inclusive o que acabou de ser usado) deixa de bater.


def _impressao_senha(usuario: Usuario) -> str:
    return hashlib.sha256(usuario.senha_hash.encode()).hexdigest()[:16]


def gerar_token_redefinicao(usuario: Usuario) -> str:
    expira_em = agora() + timedelta(minutes=MINUTOS_VALIDADE_TOKEN_SENHA)
    return criar_token(
        {
            "sub": str(usuario.idusuario),
            "finalidade": FINALIDADE_TOKEN_REDEFINIR_SENHA,
            "impressao": _impressao_senha(usuario),
            "exp": int(expira_em.timestamp()),
        }
    )


def solicitar_redefinicao_senha(payload: dict, db: Session) -> tuple[Usuario, str] | None:
    """Devolve (usuário, link) para envio do e-mail, ou None se não há conta ativa.

    A rota responde igual nos dois casos, para não revelar quais e-mails têm conta.
    """
    usuario = usuario_services.buscar_por_email(payload["email"], db)
    if not usuario or not usuario.ativo:
        return None

    link = f"{URL_FRONTEND}/redefinir-senha?token={gerar_token_redefinicao(usuario)}"
    return usuario, link


def montar_email_redefinicao(usuario: Usuario, link: str) -> tuple[str, str]:
    """(assunto, corpo em texto) do e-mail de redefinição de senha."""
    assunto = "Redefinição de senha · Mitra"
    corpo = (
        f"Olá, {usuario.nome}.\n\n"
        "Recebemos um pedido para redefinir a senha da sua conta no Mitra.\n"
        f"Para escolher uma nova senha, acesse o link abaixo "
        f"(válido por {MINUTOS_VALIDADE_TOKEN_SENHA} minutos e para um único uso):\n\n"
        f"{link}\n\n"
        "Se não foi você, ignore este e-mail: sua senha continua a mesma.\n"
    )
    return assunto, corpo


def redefinir_senha(payload: dict, db: Session) -> Usuario:
    token_invalido = HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Link de redefinição inválido ou expirado. Peça um novo.",
    )

    try:
        dados = decodificar_token(payload["token"])
    except JWTError as e:
        raise token_invalido from e

    if (
        not dados
        or dados.get("finalidade") != FINALIDADE_TOKEN_REDEFINIR_SENHA
        or "sub" not in dados
    ):
        raise token_invalido

    usuario = db.get(Usuario, int(dados["sub"]))
    if not usuario or not usuario.ativo or dados.get("impressao") != _impressao_senha(usuario):
        raise token_invalido

    usuario.senha_hash = gerar_hash_senha(payload["nova_senha"])
    db.commit()
    db.refresh(usuario)

    return usuario
