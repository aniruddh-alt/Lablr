from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_settings

# Initialize database engine and session
settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
