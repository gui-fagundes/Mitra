from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config.database import DATABASE_URL

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"


def run_migrations() -> None:
    """Aplica todas as migrations pendentes (alembic upgrade head).

    Idempotente: se o banco já está em head, é no-op.
    """
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(cfg, "head")
