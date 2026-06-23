from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

BACKEND_DIR = Path(__file__).resolve().parent


def _resolver_url(url: str) -> str:
    """Para SQLite com caminho relativo, ancora no diretório do backend.

    Evita que o banco "mude" conforme o CWD de quem subiu o servidor
    (raiz do projeto vs. pasta backend) — sempre usa backend/vanja.db.
    """
    if url.startswith("sqlite") and ":memory:" not in url:
        prefixo, _, caminho = url.partition(":///")
        if caminho and not caminho.startswith("/"):
            destino = (BACKEND_DIR / caminho.lstrip("./")).resolve()
            return f"{prefixo}:///{destino}"
    return url


DATABASE_URL = _resolver_url(settings.database_url)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
