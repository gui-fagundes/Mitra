from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.categoria_model import Categoria
from app.models.servico_model import Servico


def listar_categorias(db: Session) -> list[Categoria]:
    """Categorias ativas em ordem; os serviços ativos vêm em `servicos_ativos`."""
    return db.query(Categoria).filter(Categoria.ativo.is_(True)).order_by(Categoria.ordem).all()


def listar_servicos(db: Session, slug_categoria: str | None = None) -> list[Servico]:
    consulta = (
        db.query(Servico)
        .join(Servico.categoria)
        .filter(Servico.ativo.is_(True), Categoria.ativo.is_(True))
    )

    if slug_categoria is not None:
        categoria = (
            db.query(Categoria)
            .filter(Categoria.slug == slug_categoria, Categoria.ativo.is_(True))
            .first()
        )
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada",
            )
        consulta = consulta.filter(Servico.idcategoria == categoria.idcategoria)

    return consulta.order_by(Categoria.ordem, Servico.ordem).all()
