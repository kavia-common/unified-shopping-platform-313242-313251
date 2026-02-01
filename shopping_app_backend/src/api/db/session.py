from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.core.config import get_settings

settings = get_settings()

# SQLAlchemy 2.0 style engine
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# PUBLIC_INTERFACE
def get_db():
    """FastAPI dependency that yields a DB session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
