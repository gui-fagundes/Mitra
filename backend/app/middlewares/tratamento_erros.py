import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.config.dependencies import obter_sessao
from app.middlewares.contexto_requisicao import contexto_atual
from app.models.log_erro_model import LogErro

# O traceback completo pode ser enorme (recursão, SQL longo); o começo e o fim bastam.
TAMANHO_MAXIMO_ERRO = 8000


def _descrever(erro: Exception) -> str:
    """repr da exceção + traceback, truncado no meio se passar do limite."""
    texto = f"{erro!r}\n\n{''.join(traceback.format_exception(erro))}"
    if len(texto) <= TAMANHO_MAXIMO_ERRO:
        return texto
    metade = TAMANHO_MAXIMO_ERRO // 2
    return f"{texto[:metade]}\n\n[… {len(texto) - TAMANHO_MAXIMO_ERRO} caracteres omitidos …]\n\n{texto[-metade:]}"


def _registrar(requisicao: Request, erro: Exception) -> None:
    # Usa a mesma fábrica de sessão da API, respeitando dependency_overrides:
    # nos testes o log vai para o banco de teste, não para o de desenvolvimento.
    fabrica = requisicao.app.dependency_overrides.get(obter_sessao, obter_sessao)
    gerador = fabrica()
    db = next(gerador)
    try:
        contexto = contexto_atual()
        db.add(
            LogErro(
                rota=requisicao.url.path,
                metodo=requisicao.method,
                erro=_descrever(erro),
                idrequisicao=contexto.idrequisicao,
                ip=contexto.ip,
                idusuario=contexto.idusuario,
            )
        )
        db.commit()
    except Exception as erro_log:
        db.rollback()
        print(f"Falha ao registrar log de erro: {erro_log!r}", flush=True)
    finally:
        gerador.close()


async def capturar_excecoes(requisicao: Request, proximo):
    """Captura exceções não tratadas (RF-AD-02): registra em public.logerro e devolve
    500 padronizado. Erros de domínio (HTTPException, 4xx) não chegam aqui."""
    try:
        return await proximo(requisicao)
    except Exception as e:
        print(f"Erro não tratado capturado pelo middleware: {e!r}", flush=True)
        traceback.print_exc()
        _registrar(requisicao, e)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Ocorreu um erro inesperado no servidor. Tente novamente mais tarde."
            },
        )
