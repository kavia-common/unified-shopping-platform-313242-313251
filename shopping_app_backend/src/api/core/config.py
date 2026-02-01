import os
from dataclasses import dataclass
from typing import Optional


def _parse_db_connection_txt_line(line: str) -> Optional[str]:
    """
    Parse a db_connection.txt style line: 'psql postgresql://user:pass@host:port/db'.

    Returns the extracted SQLAlchemy-compatible URL (postgresql+psycopg://...),
    or None if parsing fails.
    """
    line = line.strip()
    if not line:
        return None
    if line.startswith("psql "):
        line = line[len("psql ") :].strip()
    if line.startswith("postgresql://"):
        # Use psycopg driver for SQLAlchemy 2.x
        return line.replace("postgresql://", "postgresql+psycopg://", 1)
    if line.startswith("postgresql+psycopg://"):
        return line
    return None


def _default_database_url() -> str:
    """
    Provide a sane local default for development based on the task-provided
    connection string. This is NOT a secret, but still allows overriding via env.
    """
    # Standardized DB port is 5000 per task. This default matches db_connection.txt.
    return "postgresql+psycopg://appuser:dbuser123@localhost:5000/myapp"


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_exp_minutes: int
    cors_allow_origins: list[str]


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load application settings from environment variables."""
    # PUBLIC_INTERFACE
    # Environment variables expected (orchestrator should set these in .env):
    # - DATABASE_URL (preferred). Example: postgresql+psycopg://user:pass@host:5000/db
    # - JWT_SECRET_KEY (required for secure deployments; dev fallback is provided)
    # - JWT_ALGORITHM (optional, default HS256)
    # - ACCESS_TOKEN_EXP_MINUTES (optional, default 60)
    # - CORS_ALLOW_ORIGINS (optional, comma separated; default '*')
    # - DB_CONNECTION_TXT (optional: raw line from db_connection.txt)
    db_connection_txt = os.getenv("DB_CONNECTION_TXT")
    parsed = _parse_db_connection_txt_line(db_connection_txt) if db_connection_txt else None

    database_url = os.getenv("DATABASE_URL") or parsed or _default_database_url()

    # WARNING: For production this must be overridden via env.
    jwt_secret_key = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-change-me")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_exp_minutes = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "60"))

    cors_raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
    cors_allow_origins = ["*"] if cors_raw.strip() == "*" else [o.strip() for o in cors_raw.split(",") if o.strip()]

    return Settings(
        database_url=database_url,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        access_token_exp_minutes=access_token_exp_minutes,
        cors_allow_origins=cors_allow_origins,
    )
