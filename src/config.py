import os
from dataclasses import dataclass

from dotenv import load_dotenv

# override=False: variáveis já definidas no ambiente (ex.: console da Lambda) prevalecem sobre o .env
load_dotenv(override=False)


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str
    connect_timeout: int


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {key}")
    return value


def load_database_settings() -> DatabaseSettings:
    return DatabaseSettings(
        host=_required("DB_HOST"),
        port=int(os.environ.get("DB_PORT", "7001")),
        name=_required("DB_NAME"),
        user=_required("DB_USER"),
        password=_required("DB_PASS"),
        connect_timeout=int(os.environ.get("DB_CONNECT_TIMEOUT", "5")),
    )
