from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.config.dependencies import obter_sessao, obter_usuario_logado
from app.models.usuario_model import Usuario
from app.schemas.prestador_schema import (
    CnpjEntrada,
    ItemPortfolioResposta,
    LegendaPortfolioAtualizacao,
    OrdemPortfolioEntrada,
    PrestadorPublicoResposta,
    ResultadoBuscaResposta,
    VitrineAtualizacao,
    VitrineCriacao,
    VitrineResposta,
)
from app.services import busca_services, portfolio_services, prestador_services
from app.services.busca_services import Ordem

# A vitrine do próprio usuário mora sob /conta, como os demais recursos do logado.
rotas_vitrine = APIRouter(prefix="/conta/vitrine", tags=["Vitrine do prestador"])
rotas_prestador = APIRouter(prefix="/prestadores", tags=["Prestadores"])


@rotas_vitrine.post("", response_model=VitrineResposta, status_code=201)
def criar_vitrine(
    corpo: VitrineCriacao,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return prestador_services.criar_vitrine(usuario_logado, corpo.model_dump(), db)


@rotas_vitrine.get("", response_model=VitrineResposta)
def obter_vitrine(usuario_logado: Usuario = Depends(obter_usuario_logado)):
    return prestador_services.obter_vitrine(usuario_logado)


@rotas_vitrine.patch("", response_model=VitrineResposta)
def atualizar_vitrine(
    corpo: VitrineAtualizacao,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return prestador_services.atualizar_vitrine(
        usuario_logado, corpo.model_dump(exclude_unset=True), db
    )


# --- CNPJ (RF-ID-07) -------------------------------------------------------------


@rotas_vitrine.put("/cnpj", response_model=VitrineResposta)
def cadastrar_cnpj(
    corpo: CnpjEntrada,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    """Só grava se a Receita (via BrasilAPI) confirmar que o CNPJ está ativo."""
    return prestador_services.cadastrar_cnpj(usuario_logado, corpo.model_dump(), db)


@rotas_vitrine.delete("/cnpj", response_model=VitrineResposta)
def remover_cnpj(
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return prestador_services.remover_cnpj(usuario_logado, db)


# --- Portfólio (RF-ID-04) ------------------------------------------------------


@rotas_vitrine.post("/portfolio", response_model=ItemPortfolioResposta, status_code=201)
def adicionar_ao_portfolio(
    arquivo: UploadFile = File(description="Imagem JPG, PNG ou WebP de até 5 MB"),
    legenda: str | None = Form(default=None, max_length=255),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return portfolio_services.adicionar(usuario_logado, arquivo, legenda, db)


@rotas_vitrine.put("/portfolio/ordem", response_model=list[ItemPortfolioResposta])
def reordenar_portfolio(
    corpo: OrdemPortfolioEntrada,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return portfolio_services.reordenar(usuario_logado, corpo.ids, db)


@rotas_vitrine.patch("/portfolio/{idprestadorportfolio}", response_model=ItemPortfolioResposta)
def editar_legenda_do_portfolio(
    idprestadorportfolio: int,
    corpo: LegendaPortfolioAtualizacao,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    return portfolio_services.editar_legenda(
        usuario_logado, idprestadorportfolio, corpo.model_dump(), db
    )


@rotas_vitrine.delete("/portfolio/{idprestadorportfolio}", status_code=204)
def remover_do_portfolio(
    idprestadorportfolio: int,
    usuario_logado: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(obter_sessao),
):
    portfolio_services.remover(usuario_logado, idprestadorportfolio, db)


# --- Busca e perfil público ----------------------------------------------------


@rotas_prestador.get("", response_model=ResultadoBuscaResposta)
def buscar_prestadores(
    termo: str | None = Query(default=None, max_length=100, description="Nome, bio ou serviço"),
    idcidade: int | None = Query(default=None, description="Prioriza (não filtra) esta cidade"),
    categoria: str | None = Query(default=None, description="Slug da categoria"),
    servicos: list[int] = Query(default=[], description="Atende ao menos um destes"),
    somente_cnpj: bool = False,
    ja_contratado: bool = Query(default=False, description="Com serviço concluído"),
    preco_min: float | None = Query(default=None, ge=0),
    preco_max: float | None = Query(default=None, ge=0),
    nota_min: float | None = Query(default=None, ge=0, le=5),
    ordem: Ordem = "reputacao",
    limite: int = Query(default=20, ge=1, le=50),
    deslocamento: int = Query(default=0, ge=0),
    db: Session = Depends(obter_sessao),
):
    """RF-BS-01 a 05. Público; ordenação orgânica, sem posições pagas."""
    return busca_services.buscar_prestadores(
        {
            "termo": termo,
            "idcidade": idcidade,
            "categoria": categoria,
            "servicos": servicos,
            "somente_cnpj": somente_cnpj,
            "ja_contratado": ja_contratado,
            "preco_min": preco_min,
            "preco_max": preco_max,
            "nota_min": nota_min,
            "ordem": ordem,
            "limite": limite,
            "deslocamento": deslocamento,
        },
        db,
    )


@rotas_prestador.get("/{idusuario}", response_model=PrestadorPublicoResposta)
def obter_prestador(idusuario: int, db: Session = Depends(obter_sessao)):
    """Perfil público (RF-BS-02). Não exige login."""
    return prestador_services.obter_prestador_publico(idusuario, db)
