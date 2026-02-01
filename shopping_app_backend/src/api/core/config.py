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


def _getenv_first(*names: str) -> Optional[str]:
    """Return the first non-empty env var value among `names`."""
    for n in names:
        v = os.getenv(n)
        if v is not None and str(v).strip() != "":
            return v
    return None


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_exp_minutes: int
    cors_allow_origins: list[str]
    backend_base_url: str
    frontend_url: str


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load application settings from environment variables.

    Env vars (preferred names per task):
    - DATABASE_URL (default: postgresql://appuser:dbuser123@localhost:5000/myapp)
    - JWT_SECRET (fallback supported: JWT_SECRET_KEY)
    - BACKEND_BASE_URL (default: http://localhost:3001)
    - FRONTEND_URL (default: http://localhost:3000)
    - CORS_ORIGINS (comma-separated; fallback supported: CORS_ALLOW_ORIGINS)
    - JWT_ALGORITHM (optional, default HS256)
    - ACCESS_TOKEN_EXP_MINUTES (optional, default 60)
    - DB_CONNECTION_TXT (optional: raw line from db_connection.txt)
    """
    # PUBLIC_INTERFACE
    # Database: allow either direct DATABASE_URL or a db_connection.txt style line.
    db_connection_txt = os.getenv("DB_CONNECTION_TXT")
    parsed = _parse_db_connection_txt_line(db_connection_txt) if db_connection_txt else None

    database_url = os.getenv("DATABASE_URL") or parsed or _default_database_url()

    # SECURITY
    # Prefer JWT_SECRET, but keep backward compatibility with JWT_SECRET_KEY.
    jwt_secret_key = _getenv_first("JWT_SECRET", "JWT_SECRET_KEY") or "dev_jwt_secret_change_me"
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_exp_minutes = int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "60"))

    # URLs
    backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:3001").rstrip("/")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

    # CORS
    cors_raw = _getenv_first("CORS_ORIGINS", "CORS_ALLOW_ORIGINS") or frontend_url
    cors_allow_origins = ["*"] if cors_raw.strip() == "*" else [o.strip() for o in cors_raw.split(",") if o.strip()]

    return Settings(
        database_url=database_url,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        access_token_exp_minutes=access_token_exp_minutes,
        cors_allow_origins=cors_allow_origins,
        backend_base_url=backend_base_url,
        frontend_url=frontend_url,
    )
