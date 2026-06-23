import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Permite importar módulos do backend sem instalar como pacote
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("SECRET_KEY", "test_secret_key")

import rate_limit  # noqa: E402
from config import settings  # noqa: E402
from db import Base, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    rate_limit.reset_state()
    # TestClient roda em http; cookie Secure não persistiria
    settings.cookie_secure = False

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def estudante(client):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "Aluno Teste",
            "email": "aluno@test.com",
            "senha": "senha123",
            "perfil": "estudante",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["usuario"]


@pytest.fixture()
def motorista(client):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "Motorista Teste",
            "email": "motorista@test.com",
            "senha": "senha123",
            "perfil": "motorista",
            "cnh": "12345678901",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["usuario"]
