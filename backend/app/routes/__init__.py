from fastapi import FastAPI

from app.routes.cidade_routes import rotas_cidade
from app.routes.conta_routes import rotas_conta
from app.routes.contratacao_routes import rotas_contratacao, rotas_contratacao_da_conversa
from app.routes.conversa_routes import rotas_conversa
from app.routes.prestador_routes import rotas_prestador, rotas_vitrine
from app.routes.taxonomia_routes import rotas_taxonomia


def registrar_rotas(app: FastAPI):
    app.include_router(rotas_conta)
    app.include_router(rotas_vitrine)
    app.include_router(rotas_prestador)
    app.include_router(rotas_conversa)
    app.include_router(rotas_contratacao_da_conversa)
    app.include_router(rotas_contratacao)
    app.include_router(rotas_cidade)
    app.include_router(rotas_taxonomia)
