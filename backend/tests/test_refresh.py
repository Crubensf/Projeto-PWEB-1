from datetime import UTC, timedelta

from security import (
    TOKEN_TYPE_ACCESS,
    create_access_token,
)


def test_login_seta_dois_cookies(client, estudante):
    client.post("/api/auth/logout")
    resp = client.post(
        "/api/auth/login",
        json={"email": estudante["email"], "senha": "senha123"},
    )
    assert resp.status_code == 200
    cookies = resp.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


def test_refresh_sem_cookie_falha(client):
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 401


def test_refresh_emite_novos_tokens(client, estudante):
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["usuario"]["email"] == estudante["email"]
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


def test_access_token_nao_serve_como_refresh(client, estudante):
    # Tenta usar o access cookie como se fosse refresh
    access = client.cookies.get("access_token")
    client.cookies.clear()
    client.cookies.set("refresh_token", access)
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 401


def test_refresh_token_nao_serve_como_access(client, estudante):
    # Tenta autenticar com refresh no slot do access
    refresh_token = client.cookies.get("refresh_token")
    client.cookies.clear()
    client.cookies.set("access_token", refresh_token)
    resp = client.get("/api/usuarios/me")
    assert resp.status_code == 401


def test_access_token_expirado_falha(client, estudante):
    # Cria access expirado e força no cookie
    expirado = create_access_token(sub=str(estudante["id"]), expires_delta=timedelta(seconds=-1))
    client.cookies.clear()
    client.cookies.set("access_token", expirado)
    resp = client.get("/api/usuarios/me")
    assert resp.status_code == 401
    assert "expirada" in resp.json()["detail"].lower()


def test_logout_limpa_ambos_cookies(client, estudante):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    # Após logout, /me e /refresh devem falhar
    client.cookies.clear()
    assert client.get("/api/usuarios/me").status_code == 401
    assert client.post("/api/auth/refresh").status_code == 401


def test_token_assinado_com_outra_chave_falha(client, estudante):
    from datetime import datetime

    from jose import jwt

    forged = jwt.encode(
        {
            "sub": str(estudante["id"]),
            "type": TOKEN_TYPE_ACCESS,
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        "chave_errada",
        algorithm="HS256",
    )
    client.cookies.clear()
    client.cookies.set("access_token", forged)
    resp = client.get("/api/usuarios/me")
    assert resp.status_code == 401
