"""Auditoria de ações sensíveis (RF-AD-02).

`registrar` só adiciona o registro à sessão: ele entra na mesma transação da ação,
então se a ação for desfeita, o registro some junto. IP e idrequisicao vêm do
contexto da requisição (middlewares/contexto_requisicao.py).

Nunca grave segredos em `dados` (senha, hash, token): só o que mudou e não é sensível.
"""

from sqlalchemy.orm import Session

from app.middlewares.contexto_requisicao import contexto_atual
from app.models.auditoria_model import Auditoria


def registrar(
    db: Session,
    acao: str,
    *,
    idusuario: int | None = None,
    entidade: str | None = None,
    identidade: int | None = None,
    dados: dict | None = None,
) -> Auditoria:
    """Acrescenta o registro à sessão, sem commit. `idusuario` padrão: o logado."""
    contexto = contexto_atual()
    registro = Auditoria(
        acao=acao,
        idusuario=idusuario if idusuario is not None else contexto.idusuario,
        entidade=entidade,
        identidade=identidade,
        dados=dados,
        ip=contexto.ip,
        idrequisicao=contexto.idrequisicao,
    )
    db.add(registro)
    return registro


def registrar_e_salvar(db: Session, acao: str, **campos) -> Auditoria:
    """Para quando o registro é a única gravação (ex.: login que falhou, que termina
    em 401): grava já, antes de a requisição terminar sem commit."""
    registro = registrar(db, acao, **campos)
    db.commit()
    return registro
