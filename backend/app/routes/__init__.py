from fastapi import FastAPI

from app.routes.auth_routes import auth_router


def register_routes(app: FastAPI):
    app.include_router(auth_router)
