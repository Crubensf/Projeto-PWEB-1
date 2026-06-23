def test_register_estudante_seta_cookie(client):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "Aluno",
            "email": "a@test.com",
            "senha": "senha123",
            "perfil": "estudante",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["usuario"]["email"] == "a@test.com"
    assert "access_token" in resp.cookies


def test_register_motorista_exige_cnh_valida(client):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "M",
            "email": "m@test.com",
            "senha": "senha123",
            "perfil": "motorista",
            "cnh": "abc",  # inválido
        },
    )
    assert resp.status_code == 400


def test_register_perfil_invalido(client):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "X",
            "email": "x@test.com",
            "senha": "senha123",
            "perfil": "admin",  # não permitido
        },
    )
    assert resp.status_code == 400


def test_register_senha_curta(client):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "Y",
            "email": "y@test.com",
            "senha": "abc",
            "perfil": "estudante",
        },
    )
    assert resp.status_code == 400


def test_register_senha_so_letras(client):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "Z",
            "email": "z@test.com",
            "senha": "apenasletras",
            "perfil": "estudante",
        },
    )
    assert resp.status_code == 400
    assert "dígito" in resp.json()["detail"]


def test_register_senha_so_digitos(client):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "W",
            "email": "w@test.com",
            "senha": "12345678",
            "perfil": "estudante",
        },
    )
    assert resp.status_code == 400
    assert "letra" in resp.json()["detail"]


def test_register_email_duplicado(client, estudante):
    resp = client.post(
        "/api/auth/register",
        data={
            "nome": "Outro",
            "email": estudante["email"],
            "senha": "senha123",
            "perfil": "estudante",
        },
    )
    assert resp.status_code == 400


def test_login_credenciais_invalidas(client, estudante):
    resp = client.post(
        "/api/auth/login",
        json={"email": estudante["email"], "senha": "errada"},
    )
    assert resp.status_code == 401


def test_login_credenciais_validas_seta_cookie(client, estudante):
    resp = client.post(
        "/api/auth/login",
        json={"email": estudante["email"], "senha": "senha123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.cookies


def test_me_sem_autenticacao(client):
    resp = client.get("/api/usuarios/me")
    assert resp.status_code == 401


def test_me_autenticado(client, estudante):
    resp = client.get("/api/usuarios/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == estudante["email"]


def test_logout_limpa_cookie(client, estudante):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    # Após logout, /me deve falhar
    client.cookies.clear()
    resp2 = client.get("/api/usuarios/me")
    assert resp2.status_code == 401
