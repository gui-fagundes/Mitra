from fastapi import FastAPI

from app.routes.conta_routes import rotas_conta


def registrar_rotas(app: FastAPI):
    app.include_router(rotas_conta)
