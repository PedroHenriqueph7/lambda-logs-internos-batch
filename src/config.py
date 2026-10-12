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
    sslmode: str = "require"


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {key}")
    return value


def _load_from_secrets_manager(secret_name: str) -> dict:
    from aws_lambda_powertools.utilities.parameters import get_secret

    secret_data = get_secret(secret_name, transform="json", max_age=300)
    if not isinstance(secret_data, dict):
        raise ValueError(f"Secret '{secret_name}' deve conter um JSON válido com as credenciais")
    return secret_data


def load_database_settings() -> DatabaseSettings:
    secret_name = os.environ.get("DB_SECRET_NAME") or os.environ.get("SECRET_NAME")

    if secret_name:
        secret_data = _load_from_secrets_manager(secret_name)
        return DatabaseSettings(
            host=os.environ.get("DB_HOST") or secret_data.get("host") or secret_data.get("endpoint", ""),
            port=int(os.environ.get("DB_PORT") or secret_data.get("port", 7001)),
            name=os.environ.get("DB_NAME") or secret_data.get("dbname") or secret_data.get("database", ""),
            user=os.environ.get("DB_USER") or secret_data.get("username") or secret_data.get("user", ""),
            password=secret_data.get("password", ""),
            connect_timeout=int(os.environ.get("DB_CONNECT_TIMEOUT", "5")),
            sslmode=os.environ.get("DB_SSLMODE", "require"),
        )

    return DatabaseSettings(
        host=_required("DB_HOST"),
        port=int(os.environ.get("DB_PORT", "7001")),
        name=_required("DB_NAME"),
        user=_required("DB_USER"),
        password=_required("DB_PASS"),
        connect_timeout=int(os.environ.get("DB_CONNECT_TIMEOUT", "5")),
        sslmode=os.environ.get("DB_SSLMODE", "require"),
    )
