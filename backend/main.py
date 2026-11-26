from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.constants import DIR_ARQUIVOS, ORIGENS_CORS, ROTA_ARQUIVOS
from app.config.migrations import aplicar_migracoes
from app.middlewares.contexto_requisicao import registrar_contexto
from app.middlewares.sessao_deslizante import renovar_sessao
from app.middlewares.tratamento_erros import capturar_excecoes
from app.routes import registrar_rotas


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    aplicar_migracoes()
    yield


app = FastAPI(title="Mitra", lifespan=ciclo_de_vida)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_CORS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ordem importa: middlewares são executados em ordem inversa da adição.
# → renovar_sessao roda por dentro de capturar_excecoes (se der 500, não renova).
# → capturar_excecoes roda por dentro do CORS (headers CORS aplicados mesmo em erro).
app.add_middleware(BaseHTTPMiddleware, dispatch=capturar_excecoes)
app.add_middleware(BaseHTTPMiddleware, dispatch=renovar_sessao)
# Por fora de todos: id e IP da requisição valem também para o log de erros.
app.add_middleware(BaseHTTPMiddleware, dispatch=registrar_contexto)

registrar_rotas(app)

# Imagens enviadas pelos usuários (ver app/utils/arquivo_utils.py).
DIR_ARQUIVOS.mkdir(parents=True, exist_ok=True)
app.mount(ROTA_ARQUIVOS, StaticFiles(directory=DIR_ARQUIVOS), name="arquivos")


@app.get("/saude")
async def verificar_saude():
    return {"status": "ok"}
