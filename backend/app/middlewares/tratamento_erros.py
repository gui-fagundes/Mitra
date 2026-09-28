import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.config.database import SessaoLocal
from app.models.log_erro_model import LogErro


async def capturar_excecoes(requisicao: Request, proximo):
    """
    Captura exceções não tratadas, registra em public.logerro e devolve 500 padronizado.
    """
    try:
        return await proximo(requisicao)
    except Exception as e:
        print(f"Erro não tratado capturado pelo middleware: {e}", flush=True)
        traceback.print_exc()

        db = SessaoLocal()
        try:
            db.add(
                LogErro(
                    rota=requisicao.url.path,
                    metodo=requisicao.method,
                    erro=str(e),
                )
            )
            db.commit()
        except Exception as erro_log:
            db.rollback()
            print(f"Falha ao registrar log de erro: {erro_log}", flush=True)
        finally:
            db.close()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Ocorreu um erro inesperado no servidor. Tente novamente mais tarde."
            },
        )
