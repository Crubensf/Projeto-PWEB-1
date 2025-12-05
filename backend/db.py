# backend/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./vanja.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependência para obter a sessão de banco via FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Cria as tabelas quando o módulo for importado
Base.metadata.create_all(bind=engine)
