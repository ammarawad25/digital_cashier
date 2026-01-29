from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .database import Base
from ..config import settings

# Optimized connection pooling for better performance
engine = create_engine(
    settings.database_url,
    echo=False,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to keep open
    max_overflow=20,  # Additional connections when needed
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
