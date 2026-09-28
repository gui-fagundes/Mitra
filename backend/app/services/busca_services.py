"""Busca de prestadores (RF-BS-01 a 05) com ordenação orgânica — sem posições pagas."""

from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, Float, case, exists, false, func, literal, or_
from sqlalchemy.orm import Session

from app.models.categoria_model import Categoria
from app.models.contratacao_model import Contratacao
from app.models.conversa_model import Conversa
from app.models.prestador_perfil_model import PrestadorPerfil
from app.models.prestador_servico_model import PrestadorServico
from app.models.servico_model import Servico
from app.models.usuario_model import Usuario
from app.utils.data_utils import agora

Ordem = Literal["reputacao", "melhor", "muitas", "recentes"]

# Pesos da reputação (docs: "Ordenação orgânica"). Somam 1.
PESO_NOTA = 0.6
PESO_VOLUME = 0.3
PESO_ATIVIDADE = 0.1
# Atividade vai de 1 (acessou agora) a 0 (sumido há DIAS_ATIVIDADE dias ou mais).
DIAS_ATIVIDADE = 90


def _atividade(momento: datetime):
    """1 - dias desde o último acesso / DIAS_ATIVIDADE, limitada a [0, 1]. Nunca acessou = 0."""
    dias = func.extract("epoch", literal(momento, DateTime) - Usuario.ultimo_acesso_em) / 86400.0
    return func.coalesce(func.greatest(0.0, 1.0 - dias / DIAS_ATIVIDADE), 0.0)


def _nota_media():
    # Etapa de avaliações: AVG(avaliacao.nota) do prestador. Enquanto não existe, NULL.
    return literal(None, Float)


def _qtd_avaliacoes():
    # Etapa de avaliações: COUNT(avaliacao) do prestador.
    return literal(0)


def pontuacao_reputacao(momento: datetime):
    """Único lugar da fórmula de ranking — trocar pesos ou termos é aqui.

    score = nota/5 · 0,6 + min(log(1+qtd)/log(1+50), 1) · 0,3 + atividade · 0,1
    """
    nota = func.coalesce(_nota_media(), 0.0) / 5.0
    volume = func.least(func.ln(1 + _qtd_avaliacoes()) / func.ln(51.0), 1.0)
    return nota * PESO_NOTA + volume * PESO_VOLUME + _atividade(momento) * PESO_ATIVIDADE


def _termo_como_padrao(termo: str) -> str:
    """Normaliza espaços e escapa curingas do LIKE: "  el_é  " → "%el\\_é%"."""
    limpo = " ".join(termo.split())
    escapado = limpo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def _atende(*condicoes):
    """EXISTS: o prestador atende algum serviço que satisfaz as condições."""
    return exists().where(
        PrestadorServico.idprestadorperfil == PrestadorPerfil.idprestadorperfil,
        PrestadorServico.idservico == Servico.idservico,
        Servico.ativo.is_(True),
        *condicoes,
    )


def buscar_prestadores(filtros: dict, db: Session) -> dict:
    """Devolve {"total": n, "itens": [...]} com os cards da página pedida."""
    momento = agora()

    consulta = (
        db.query(PrestadorPerfil)
        .join(Usuario, Usuario.idusuario == PrestadorPerfil.idusuario)
        # Visibilidade: conta ativa e ao menos um serviço (docs: "Regra de visibilidade").
        .filter(Usuario.ativo.is_(True), _atende())
    )

    termo = (filtros.get("termo") or "").strip()
    if termo:
        padrao = _termo_como_padrao(termo)
        consulta = consulta.filter(
            or_(
                Usuario.nome.ilike(padrao, escape="\\"),
                PrestadorPerfil.bio.ilike(padrao, escape="\\"),
                _atende(Servico.nome.ilike(padrao, escape="\\")),
            )
        )

    if filtros.get("categoria"):
        consulta = consulta.filter(
            _atende(
                Servico.idcategoria == Categoria.idcategoria,
                Categoria.slug == filtros["categoria"],
                Categoria.ativo.is_(True),
            )
        )

    if filtros.get("servicos"):
        consulta = consulta.filter(_atende(Servico.idservico.in_(filtros["servicos"])))

    if filtros.get("ja_contratado"):
        # Ao menos um serviço concluído (confirmado pelos dois lados) como prestador.
        consulta = consulta.filter(
            exists().where(
                Conversa.idprestador == PrestadorPerfil.idusuario,
                Contratacao.idconversa == Conversa.idconversa,
                Contratacao.estado == "concluido",
            )
        )

    if filtros.get("somente_cnpj"):
        consulta = consulta.filter(PrestadorPerfil.cnpj.is_not(None))

    # Faixas que se sobrepõem; "sob consulta" (sem preço) nunca é excluído.
    if filtros.get("preco_min") is not None:
        consulta = consulta.filter(
            or_(
                PrestadorPerfil.preco_max.is_(None),
                PrestadorPerfil.preco_max >= filtros["preco_min"],
            )
        )
    if filtros.get("preco_max") is not None:
        consulta = consulta.filter(
            or_(
                PrestadorPerfil.preco_min.is_(None),
                PrestadorPerfil.preco_min <= filtros["preco_max"],
            )
        )

    if filtros.get("nota_min"):
        # Sem avaliações ainda, ninguém atinge uma nota mínima.
        # Etapa de avaliações: filtrar por _nota_media() >= nota_min.
        consulta = consulta.filter(false())

    total = consulta.count()

    # idcidade não filtra: prioriza quem é da cidade (decisão de modelagem).
    ordenacao = []
    if filtros.get("idcidade") is not None:
        ordenacao.append(case((Usuario.idcidade == filtros["idcidade"], 0), else_=1))

    score = pontuacao_reputacao(momento)
    ordem: Ordem = filtros.get("ordem") or "reputacao"
    if ordem == "melhor":
        ordenacao += [_nota_media().desc().nulls_last(), score.desc()]
    elif ordem == "muitas":
        ordenacao += [_qtd_avaliacoes().desc(), score.desc()]
    elif ordem == "recentes":
        ordenacao.append(PrestadorPerfil.criado_em.desc())
    else:
        ordenacao.append(score.desc())
    # Desempate estável, para a paginação não repetir nem pular ninguém.
    ordenacao += [PrestadorPerfil.criado_em.desc(), PrestadorPerfil.idprestadorperfil.desc()]

    perfis = (
        consulta.order_by(*ordenacao)
        .offset(filtros.get("deslocamento", 0))
        .limit(filtros.get("limite", 20))
        .all()
    )

    return {"total": total, "itens": [_cartao(perfil) for perfil in perfis]}


def _cartao(perfil: PrestadorPerfil) -> dict:
    usuario = perfil.usuario
    return {
        "idusuario": usuario.idusuario,
        "nome": usuario.nome,
        "foto_url": usuario.foto_url,
        "cidade": usuario.cidade,
        "bio": perfil.bio,
        "preco_min": perfil.preco_min,
        "preco_max": perfil.preco_max,
        "cnpj_validado": perfil.cnpj_validado,
        "servicos": perfil.servicos_ordenados,
        "ultimo_acesso_em": usuario.ultimo_acesso_em,
        # Preenchidos pela etapa de avaliações.
        "nota_media": None,
        "qtd_avaliacoes": 0,
    }
