from datetime import date, timedelta

import pytest

ROTA_TODOS_DIAS = {
    "nome": "Centro → UFPI",
    "origem": "Centro",
    "destino": "UFPI",
    "hora_ida": "07:00",
    "hora_volta": "18:00",
    "vagas": 2,
    "veiculo": "Van",
    "dias_semana": ["seg", "ter", "qua", "qui", "sex", "sab", "dom"],
    "preco": 150.0,
}


def proxima_data():
    """Sempre amanhã — qualquer dia da semana é válido em ROTA_TODOS_DIAS."""
    return (date.today() + timedelta(days=1)).isoformat()


def _criar_rota(client, motorista, payload=ROTA_TODOS_DIAS):
    resp = client.post("/api/motorista/rotas", json=payload)
    assert resp.status_code == 200, resp.text
    rota = resp.json()
    # Loga estudante de volta — fixture motorista deixou ele logado
    client.post("/api/auth/logout")
    return rota


def _login_estudante(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "aluno@test.com", "senha": "senha123"},
    )
    assert resp.status_code == 200, resp.text


@pytest.fixture()
def cenario(client, estudante, motorista):
    """Motorista com 1 rota e estudante logado pronto pra reservar."""
    rota = _criar_rota(client, motorista)
    _login_estudante(client)
    return {"rota": rota, "estudante": estudante, "motorista": motorista}


def test_reservar_viagem_ok(client, cenario):
    resp = client.post(
        "/api/estudante/viagens",
        json={"rota_id": cenario["rota"]["id"], "data": proxima_data()},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "reservada"
    assert body["rota"]["id"] == cenario["rota"]["id"]


def test_listar_minhas_viagens(client, cenario):
    client.post(
        "/api/estudante/viagens",
        json={"rota_id": cenario["rota"]["id"], "data": proxima_data()},
    )
    resp = client.get("/api/estudante/viagens")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_reservar_data_passada(client, cenario):
    ontem = (date.today() - timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/estudante/viagens",
        json={"rota_id": cenario["rota"]["id"], "data": ontem},
    )
    assert resp.status_code == 400


def test_reservar_dia_invalido(client, estudante, motorista):
    # Rota só na segunda
    rota_payload = {**ROTA_TODOS_DIAS, "dias_semana": ["seg"]}
    rota = _criar_rota(client, motorista, rota_payload)
    _login_estudante(client)

    # Pega o próximo domingo
    hoje = date.today()
    dias_ate_dom = (6 - hoje.weekday()) % 7 or 7
    domingo = hoje + timedelta(days=dias_ate_dom)

    resp = client.post(
        "/api/estudante/viagens",
        json={"rota_id": rota["id"], "data": domingo.isoformat()},
    )
    assert resp.status_code == 400


def test_reservar_rota_inexistente(client, estudante):
    resp = client.post(
        "/api/estudante/viagens",
        json={"rota_id": 9999, "data": proxima_data()},
    )
    assert resp.status_code == 404


def test_reserva_duplicada(client, cenario):
    payload = {"rota_id": cenario["rota"]["id"], "data": proxima_data()}
    r1 = client.post("/api/estudante/viagens", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/estudante/viagens", json=payload)
    assert r2.status_code == 400


def test_capacidade_esgotada(client, estudante, motorista):
    # Rota com 1 vaga só
    rota_payload = {**ROTA_TODOS_DIAS, "vagas": 1}
    rota = _criar_rota(client, motorista, rota_payload)

    # Primeiro estudante reserva
    _login_estudante(client)
    r1 = client.post(
        "/api/estudante/viagens",
        json={"rota_id": rota["id"], "data": proxima_data()},
    )
    assert r1.status_code == 201
    client.post("/api/auth/logout")

    # Segundo estudante tenta reservar a mesma vaga
    client.post(
        "/api/auth/register",
        data={
            "nome": "Outro Aluno",
            "email": "outro@test.com",
            "senha": "senha123",
            "perfil": "estudante",
        },
    )
    r2 = client.post(
        "/api/estudante/viagens",
        json={"rota_id": rota["id"], "data": proxima_data()},
    )
    assert r2.status_code == 409


def test_cancelar_propria_viagem(client, cenario):
    criada = client.post(
        "/api/estudante/viagens",
        json={"rota_id": cenario["rota"]["id"], "data": proxima_data()},
    ).json()
    resp = client.delete(f"/api/estudante/viagens/{criada['id']}")
    assert resp.status_code == 204

    # Status deve ter virado cancelada
    lista = client.get("/api/estudante/viagens").json()
    assert lista[0]["status"] == "cancelada"


def test_cancelar_libera_vaga(client, estudante, motorista):
    rota_payload = {**ROTA_TODOS_DIAS, "vagas": 1}
    rota = _criar_rota(client, motorista, rota_payload)

    _login_estudante(client)
    criada = client.post(
        "/api/estudante/viagens",
        json={"rota_id": rota["id"], "data": proxima_data()},
    ).json()
    client.delete(f"/api/estudante/viagens/{criada['id']}")

    # Agora outro estudante consegue reservar
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/register",
        data={
            "nome": "Outro",
            "email": "outro@test.com",
            "senha": "senha123",
            "perfil": "estudante",
        },
    )
    resp = client.post(
        "/api/estudante/viagens",
        json={"rota_id": rota["id"], "data": proxima_data()},
    )
    assert resp.status_code == 201


def test_motorista_nao_pode_reservar(client, motorista):
    resp = client.post(
        "/api/estudante/viagens",
        json={"rota_id": 1, "data": proxima_data()},
    )
    assert resp.status_code == 403


def test_estudante_nao_ve_endpoint_motorista(client, estudante):
    resp = client.put("/api/motorista/viagens/1", json={"status": "realizada"})
    assert resp.status_code == 403


def test_motorista_marca_realizada(client, cenario):
    # Estudante reserva, motorista finaliza
    criada = client.post(
        "/api/estudante/viagens",
        json={"rota_id": cenario["rota"]["id"], "data": proxima_data()},
    ).json()
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={"email": "motorista@test.com", "senha": "senha123"},
    )

    resp = client.put(
        f"/api/motorista/viagens/{criada['id']}",
        json={"status": "realizada"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "realizada"


def test_motorista_nao_finaliza_viagem_de_outro(client, estudante, motorista):
    # Motorista A cria rota e estudante reserva
    rota = _criar_rota(client, motorista)
    _login_estudante(client)
    criada = client.post(
        "/api/estudante/viagens",
        json={"rota_id": rota["id"], "data": proxima_data()},
    ).json()

    # Motorista B se cadastra e tenta finalizar
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/register",
        data={
            "nome": "Outro Motorista",
            "email": "motorista2@test.com",
            "senha": "senha123",
            "perfil": "motorista",
            "cnh": "98765432101",
        },
    )
    resp = client.put(
        f"/api/motorista/viagens/{criada['id']}",
        json={"status": "realizada"},
    )
    assert resp.status_code == 404
