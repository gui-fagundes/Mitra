import os

TOKEN_EXPIRATION_TIME = 60  # minutos

ACCESS_TOKEN_COOKIE = "access_token"

ENV = os.getenv("ENV", "development").lower()
IS_PRODUCTION = ENV == "production"

CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]
