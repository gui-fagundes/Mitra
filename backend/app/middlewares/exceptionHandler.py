import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.config.database import SessionLocal
from app.models.log_erro_model import LogErro
from app.utils.datetime_utils import get_now


async def catch_exceptions_middleware(request: Request, call_next):
    """
    Captura exceções não tratadas, registra em public.logerro e devolve 500 padronizado.
    """
    try:
        return await call_next(request)
    except Exception as e:
        print(f"Erro não tratado capturado pelo middleware: {e}")
        traceback.print_exc()

        db = SessionLocal()
        try:
            erro = LogErro(
                endpoint=request.url.path,
                metodo=request.method,
                datahora=get_now(),
                erro=str(e),
            )
            db.add(erro)
            db.commit()
        except Exception as log_err:
            db.rollback()
            print(f"Falha ao registrar log de erro: {log_err}")
        finally:
            db.close()

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Ocorreu um erro inesperado no servidor. Tente novamente mais tarde."
            },
        )
