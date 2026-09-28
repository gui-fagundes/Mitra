from fastapi import FastAPI

from app.routes.cidade_routes import rotas_cidade
from app.routes.conta_routes import rotas_conta
from app.routes.taxonomia_routes import rotas_taxonomia


def registrar_rotas(app: FastAPI):
    app.include_router(rotas_conta)
    app.include_router(rotas_cidade)
    app.include_router(rotas_taxonomia)
