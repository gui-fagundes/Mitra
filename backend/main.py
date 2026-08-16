from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.constants import CORS_ORIGINS
from app.config.migrations import run_migrations
from app.middlewares.exceptionHandler import catch_exceptions_middleware
from app.middlewares.sliding_session import sliding_session_middleware
from app.routes import register_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


app = FastAPI(title="Mitra", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ordem importa: middlewares são executados em ordem inversa da adição.
# → sliding_session roda por dentro do exception_handler (se der 500, não renova).
# → exception_handler roda por dentro do CORS (headers CORS aplicados mesmo em erro).
app.add_middleware(BaseHTTPMiddleware, dispatch=catch_exceptions_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=sliding_session_middleware)

register_routes(app)


@app.get("/health-check")
async def health_check():
    return {"status": "ok"}
