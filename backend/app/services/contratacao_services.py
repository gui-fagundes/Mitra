"""Contratação combinada dentro da conversa (RF-CO-01, RF-CO-04).

    proposta ──(aceite dos dois)──▶ combinado ──(conclusão confirmada pelos dois)──▶ concluido
        └───────────────┬────────────────┘
                        ▼
                    cancelado

Regras que não podem escapar:
- só os dois participantes da conversa leem ou mexem;
- no máximo uma contratação aberta (proposta/combinado) por conversa;
- quem propõe ou edita a proposta já aceita aquela versão; o aceite do outro cai;
- na conclusão, quem informa ou muda o preço cobrado confirma; a confirmação do outro cai;
- cada transição vira um evento na conversa (histórico registrado no Mitra).
"""

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.contratacao_model import ESTADOS_ABERTOS, Contratacao
from app.models.conversa_model import Conversa
from app.models.servico_model import Servico
from app.models.usuario_model import Usuario
from app.services import conversa_services
from app.utils.data_utils import agora

CAMPOS_PROPOSTA = ("idservico", "descricao", "local", "data_prevista", "valor_estimado")

_JA_HA_ABERTA = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Já há uma proposta em andamento nesta conversa",
)


def _reais(valor: Decimal | float) -> str:
    """Decimal("1240.5") → "R$ 1.240,50"."""
    texto = f"{Decimal(valor):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _texto_opcional(texto: str | None) -> str | None:
    if texto is None:
        return None
    return texto.strip() or None


def _descricao(texto: str) -> str:
    descricao = texto.strip()
    if not descricao:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A descrição não pode ficar em branco",
        )
    return descricao


def _servico_ativo(idservico: int, db: Session) -> Servico:
    servico = db.get(Servico, idservico)
    if not servico or not servico.ativo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Serviço inválido",
        )
    return servico


def _obter(usuario: Usuario, idcontratacao: int, db: Session) -> Contratacao:
    contratacao = db.get(Contratacao, idcontratacao)
    if contratacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratação não encontrada",
        )
    if not contratacao.conversa.participa(usuario.idusuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não participa desta contratação",
        )
    return contratacao


def _exigir_estado(contratacao: Contratacao, *estados: str, acao: str) -> None:
    if contratacao.estado not in estados:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não é possível {acao}: a contratação está {contratacao.estado}",
        )


def _evento(contratacao: Contratacao, autor: Usuario, texto: str, db: Session) -> None:
    conversa_services.adicionar_mensagem(
        contratacao.conversa,
        autor.idusuario,
        texto,
        db,
        tipo="evento",
        idcontratacao=contratacao.idcontratacao,
    )


def _campo_do_papel(contratacao: Contratacao, usuario: Usuario, prefixo: str) -> str:
    """ "aceite" + cliente → "aceite_cliente_em"."""
    return f"{prefixo}_{contratacao.papel_de(usuario.idusuario)}_em"


def _campo_do_outro(contratacao: Contratacao, usuario: Usuario, prefixo: str) -> str:
    outro = "prestador" if contratacao.papel_de(usuario.idusuario) == "cliente" else "cliente"
    return f"{prefixo}_{outro}_em"


def _aguardando(contratacao: Contratacao, usuario: Usuario) -> bool:
    if contratacao.estado == "proposta":
        return getattr(contratacao, _campo_do_papel(contratacao, usuario, "aceite")) is None
    if contratacao.estado == "combinado":
        return getattr(contratacao, _campo_do_papel(contratacao, usuario, "conclusao")) is None
    return False


def resumo(contratacao: Contratacao, usuario: Usuario) -> dict:
    """A contratação do ponto de vista de quem está vendo."""
    dados = {
        coluna: getattr(contratacao, coluna) for coluna in Contratacao.__table__.columns.keys()
    }
    dados.update(
        papel=contratacao.papel_de(usuario.idusuario),
        outra_parte=contratacao.conversa.outra_parte(usuario.idusuario),
        servico=contratacao.servico,
        aguardando_voce=_aguardando(contratacao, usuario),
    )
    return dados


def _salvar(contratacao: Contratacao, db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as e:
        # Outra proposta foi aberta na mesma conversa ao mesmo tempo.
        db.rollback()
        raise _JA_HA_ABERTA from e
    db.refresh(contratacao)


# --- Proposta ---------------------------------------------------------------------


def propor(usuario: Usuario, idconversa: int, payload: dict, db: Session) -> dict:
    conversa = conversa_services.obter_participando(idconversa, usuario, db)
    aberta = (
        db.query(Contratacao)
        .filter(Contratacao.idconversa == idconversa, Contratacao.estado.in_(ESTADOS_ABERTOS))
        .first()
    )
    if aberta:
        raise _JA_HA_ABERTA

    servico = _servico_ativo(payload["idservico"], db)
    contratacao = Contratacao(
        conversa=conversa,
        idproponente=usuario.idusuario,
        idservico=servico.idservico,
        descricao=_descricao(payload["descricao"]),
        local=_texto_opcional(payload.get("local")),
        data_prevista=payload.get("data_prevista"),
        valor_estimado=payload.get("valor_estimado"),
        estado="proposta",
    )
    db.add(contratacao)
    setattr(contratacao, _campo_do_papel(contratacao, usuario, "aceite"), agora())
    db.flush()
    _evento(contratacao, usuario, f"{usuario.nome} propôs um serviço: {servico.nome}", db)
    _salvar(contratacao, db)
    return resumo(contratacao, usuario)


def editar_proposta(usuario: Usuario, idcontratacao: int, payload: dict, db: Session) -> dict:
    """`payload` só com os campos enviados (exclude_unset)."""
    contratacao = _obter(usuario, idcontratacao, db)
    _exigir_estado(contratacao, "proposta", acao="editar a proposta")

    if payload.get("idservico") is not None:
        _servico_ativo(payload["idservico"], db)
    if "descricao" in payload:
        payload["descricao"] = _descricao(payload["descricao"])
    if "local" in payload:
        payload["local"] = _texto_opcional(payload["local"])

    mudou = False
    for campo in CAMPOS_PROPOSTA:
        if campo in payload and getattr(contratacao, campo) != payload[campo]:
            setattr(contratacao, campo, payload[campo])
            mudou = True
    if not mudou:
        return resumo(contratacao, usuario)

    # Nova versão: quem editou aceita; o outro precisa aceitar de novo.
    setattr(contratacao, _campo_do_papel(contratacao, usuario, "aceite"), agora())
    setattr(contratacao, _campo_do_outro(contratacao, usuario, "aceite"), None)
    _evento(contratacao, usuario, f"{usuario.nome} alterou a proposta", db)
    _salvar(contratacao, db)
    return resumo(contratacao, usuario)


def aceitar(usuario: Usuario, idcontratacao: int, db: Session) -> dict:
    contratacao = _obter(usuario, idcontratacao, db)
    _exigir_estado(contratacao, "proposta", acao="aceitar")

    campo = _campo_do_papel(contratacao, usuario, "aceite")
    if getattr(contratacao, campo) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já aceitou esta versão da proposta",
        )
    momento = agora()
    setattr(contratacao, campo, momento)

    if contratacao.aceite_cliente_em and contratacao.aceite_prestador_em:
        contratacao.estado = "combinado"
        contratacao.combinado_em = momento
        _evento(contratacao, usuario, "Plano combinado: os dois aceitaram a proposta", db)
    else:
        _evento(contratacao, usuario, f"{usuario.nome} aceitou a proposta", db)
    _salvar(contratacao, db)
    return resumo(contratacao, usuario)


# --- Conclusão --------------------------------------------------------------------


def confirmar_conclusao(usuario: Usuario, idcontratacao: int, payload: dict, db: Session) -> dict:
    contratacao = _obter(usuario, idcontratacao, db)
    _exigir_estado(contratacao, "combinado", acao="confirmar a conclusão")

    novo_valor = payload.get("valor_final")
    if novo_valor is None and contratacao.valor_final is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Informe o preço cobrado para confirmar a conclusão",
        )

    meu_campo = _campo_do_papel(contratacao, usuario, "conclusao")
    mudou_valor = novo_valor is not None and novo_valor != contratacao.valor_final
    if getattr(contratacao, meu_campo) is not None and not mudou_valor:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já confirmou a conclusão",
        )

    momento = agora()
    if mudou_valor:
        contratacao.valor_final = novo_valor
        # O outro lado confirmou outro valor: precisa confirmar de novo.
        setattr(contratacao, _campo_do_outro(contratacao, usuario, "conclusao"), None)
    setattr(contratacao, meu_campo, momento)

    valor = _reais(contratacao.valor_final)
    if contratacao.conclusao_cliente_em and contratacao.conclusao_prestador_em:
        contratacao.estado = "concluido"
        contratacao.concluido_em = momento
        _evento(
            contratacao,
            usuario,
            f"Serviço concluído ({valor}): os dois confirmaram. A avaliação está liberada.",
            db,
        )
    else:
        _evento(contratacao, usuario, f"{usuario.nome} confirmou a conclusão ({valor})", db)
    _salvar(contratacao, db)
    return resumo(contratacao, usuario)


# --- Cancelamento -----------------------------------------------------------------


def cancelar(usuario: Usuario, idcontratacao: int, payload: dict, db: Session) -> dict:
    contratacao = _obter(usuario, idcontratacao, db)
    _exigir_estado(contratacao, *ESTADOS_ABERTOS, acao="cancelar")

    motivo = _texto_opcional(payload.get("motivo"))
    contratacao.estado = "cancelado"
    contratacao.cancelado_em = agora()
    contratacao.idcancelado_por = usuario.idusuario
    contratacao.motivo_cancelamento = motivo

    acao = "recusou a proposta" if contratacao.combinado_em is None else "cancelou o serviço"
    _evento(
        contratacao,
        usuario,
        f"{usuario.nome} {acao}" + (f": {motivo}" if motivo else ""),
        db,
    )
    _salvar(contratacao, db)
    return resumo(contratacao, usuario)


# --- Consultas ----------------------------------------------------------------------


def obter(usuario: Usuario, idcontratacao: int, db: Session) -> dict:
    return resumo(_obter(usuario, idcontratacao, db), usuario)


def listar_da_conversa(usuario: Usuario, idconversa: int, db: Session) -> list[dict]:
    conversa_services.obter_participando(idconversa, usuario, db)
    contratacoes = (
        db.query(Contratacao)
        .filter(Contratacao.idconversa == idconversa)
        .order_by(Contratacao.criado_em.desc(), Contratacao.idcontratacao.desc())
        .all()
    )
    return [resumo(c, usuario) for c in contratacoes]


def listar_minhas(
    usuario: Usuario, db: Session, papel: str = "todos", estado: str | None = None
) -> list[dict]:
    """Contratações em que o usuário é cliente, prestador ou os dois papéis."""
    consulta = db.query(Contratacao).join(Conversa, Conversa.idconversa == Contratacao.idconversa)
    if papel == "cliente":
        consulta = consulta.filter(Conversa.idcliente == usuario.idusuario)
    elif papel == "prestador":
        consulta = consulta.filter(Conversa.idprestador == usuario.idusuario)
    else:
        consulta = consulta.filter(
            or_(Conversa.idcliente == usuario.idusuario, Conversa.idprestador == usuario.idusuario)
        )
    if estado:
        consulta = consulta.filter(Contratacao.estado == estado)

    contratacoes = consulta.order_by(
        Contratacao.atualizado_em.desc(), Contratacao.idcontratacao.desc()
    ).all()
    return [resumo(c, usuario) for c in contratacoes]
