"""Exportação dos dados pessoais do titular (LGPD, RF-DP-02).

Regras:
- tudo o que é do titular vai completo (conta, vitrine, mensagens que ele enviou,
  propostas e contratações de que participou, avaliações feitas e recebidas);
- conteúdo escrito por terceiros não vai: das mensagens recebidas, só data e remetente.
  Eventos automáticos do chat vão com texto (são gerados pelo sistema);
- imagens (foto e portfólio) vão como links absolutos, não como arquivos.
"""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.avaliacao_model import Avaliacao
from app.models.contratacao_model import Contratacao
from app.models.conversa_model import Conversa
from app.models.mensagem_model import Mensagem
from app.models.usuario_model import Usuario
from app.services.avaliacao_services import nome_abreviado
from app.utils.data_utils import agora

AVISO = (
    "Dados pessoais mantidos pelo Mitra sobre o titular (LGPD, art. 18, II). "
    "Mensagens recebidas aparecem sem o conteúdo, que é dado pessoal de quem as escreveu. "
    "Foto e portfólio aparecem como links para os arquivos."
)


def _link(url_base: str, caminho: str | None) -> str | None:
    """ "/arquivos/fotos/x.jpg" → "https://api…/arquivos/fotos/x.jpg"."""
    if not caminho:
        return None
    if caminho.startswith(("http://", "https://")):
        return caminho
    return url_base.rstrip("/") + caminho


def _conta(usuario: Usuario, url_base: str) -> dict:
    return {
        "idusuario": usuario.idusuario,
        "nome": usuario.nome,
        "email": usuario.email,
        "telefone": usuario.telefone,
        "cidade": f"{usuario.cidade.nome}/{usuario.cidade.uf}" if usuario.cidade else None,
        "foto_url": _link(url_base, usuario.foto_url),
        "notificar_email": usuario.notificar_email,
        "busca_somente_cnpj": usuario.busca_somente_cnpj,
        "aceite_termos_em": usuario.aceite_termos_em,
        "email_verificado_em": usuario.email_verificado_em,
        "criado_em": usuario.criado_em,
        "ultimo_acesso_em": usuario.ultimo_acesso_em,
        "ativo": usuario.ativo,
    }


def _perfil_prestador(usuario: Usuario, url_base: str) -> dict | None:
    perfil = usuario.prestador_perfil
    if perfil is None:
        return None
    return {
        "bio": perfil.bio,
        "preco_min": perfil.preco_min,
        "preco_max": perfil.preco_max,
        "disponibilidade": perfil.disponibilidade,
        "cnpj": perfil.cnpj,
        "cnpj_validado_em": perfil.cnpj_validado_em,
        "servicos": [s.nome for s in perfil.servicos_ordenados],
        "portfolio": [
            {
                "imagem_url": _link(url_base, item.imagem_url),
                "legenda": item.legenda,
                "ordem": item.ordem,
                "criado_em": item.criado_em,
            }
            for item in perfil.portfolio
        ],
        "criado_em": perfil.criado_em,
        "atualizado_em": perfil.atualizado_em,
    }


def _mensagem(mensagem: Mensagem, idusuario: int) -> dict:
    if mensagem.tipo == "evento":
        return {"enviada_em": mensagem.criado_em, "tipo": "evento", "texto": mensagem.texto}
    if mensagem.idautor == idusuario:
        return {"enviada_em": mensagem.criado_em, "de": "você", "texto": mensagem.texto}
    return {"enviada_em": mensagem.criado_em, "de": "outra parte", "texto": None}


def _conversas(usuario: Usuario, db: Session) -> list[dict]:
    conversas = (
        db.query(Conversa)
        .filter(
            or_(Conversa.idcliente == usuario.idusuario, Conversa.idprestador == usuario.idusuario)
        )
        .order_by(Conversa.criado_em)
        .all()
    )
    resultado = []
    for conversa in conversas:
        mensagens = (
            db.query(Mensagem)
            .filter(Mensagem.idconversa == conversa.idconversa)
            .order_by(Mensagem.idmensagem)
            .all()
        )
        resultado.append(
            {
                "idconversa": conversa.idconversa,
                "seu_papel": "cliente" if conversa.idcliente == usuario.idusuario else "prestador",
                "com": conversa.outra_parte(usuario.idusuario).nome,
                "iniciada_em": conversa.criado_em,
                "mensagens": [_mensagem(m, usuario.idusuario) for m in mensagens],
            }
        )
    return resultado


def _contratacoes(usuario: Usuario, db: Session) -> list[dict]:
    """Propostas e contratações de que o titular participou (dados do contrato entre as partes)."""
    contratacoes = (
        db.query(Contratacao)
        .join(Conversa, Conversa.idconversa == Contratacao.idconversa)
        .filter(
            or_(Conversa.idcliente == usuario.idusuario, Conversa.idprestador == usuario.idusuario)
        )
        .order_by(Contratacao.criado_em)
        .all()
    )
    return [
        {
            "idcontratacao": c.idcontratacao,
            "seu_papel": c.papel_de(usuario.idusuario),
            "com": c.conversa.outra_parte(usuario.idusuario).nome,
            "proposta_por": "você" if c.idproponente == usuario.idusuario else "outra parte",
            "servico": c.servico.nome,
            "descricao": c.descricao,
            "local": c.local,
            "data_prevista": c.data_prevista,
            "valor_estimado": c.valor_estimado,
            "estado": c.estado,
            "aceite_cliente_em": c.aceite_cliente_em,
            "aceite_prestador_em": c.aceite_prestador_em,
            "combinado_em": c.combinado_em,
            "valor_final": c.valor_final,
            "conclusao_cliente_em": c.conclusao_cliente_em,
            "conclusao_prestador_em": c.conclusao_prestador_em,
            "concluido_em": c.concluido_em,
            "cancelado_em": c.cancelado_em,
            "criado_em": c.criado_em,
        }
        for c in contratacoes
    ]


def _avaliacoes(usuario: Usuario, db: Session) -> tuple[list[dict], list[dict]]:
    avaliacoes = (
        db.query(Avaliacao)
        .join(Contratacao, Contratacao.idcontratacao == Avaliacao.idcontratacao)
        .join(Conversa, Conversa.idconversa == Contratacao.idconversa)
        .filter(
            or_(Conversa.idcliente == usuario.idusuario, Conversa.idprestador == usuario.idusuario)
        )
        .order_by(Avaliacao.criado_em)
        .all()
    )
    feitas, recebidas = [], []
    for a in avaliacoes:
        conversa = a.contratacao.conversa
        if conversa.idcliente == usuario.idusuario:
            # A resposta foi escrita pelo prestador (terceiro): só a data.
            feitas.append(
                {
                    "prestador": conversa.prestador.nome,
                    "servico": a.contratacao.servico.nome,
                    "nota": a.nota,
                    "comentario": a.comentario,
                    "criado_em": a.criado_em,
                    "respondida_em": a.resposta_em,
                }
            )
        else:
            # Avaliação sobre o titular (já pública no perfil dele), com autor abreviado.
            recebidas.append(
                {
                    "autor": nome_abreviado(conversa.cliente.nome),
                    "servico": a.contratacao.servico.nome,
                    "nota": a.nota,
                    "comentario": a.comentario,
                    "criado_em": a.criado_em,
                    "sua_resposta": a.resposta,
                    "respondida_em": a.resposta_em,
                }
            )
    return feitas, recebidas


def exportar(usuario: Usuario, url_base: str, db: Session) -> dict:
    feitas, recebidas = _avaliacoes(usuario, db)
    return {
        "gerado_em": agora(),
        "sobre": AVISO,
        "conta": _conta(usuario, url_base),
        "perfil_prestador": _perfil_prestador(usuario, url_base),
        "conversas": _conversas(usuario, db),
        "contratacoes": _contratacoes(usuario, db),
        "avaliacoes_feitas": feitas,
        "avaliacoes_recebidas": recebidas,
    }
