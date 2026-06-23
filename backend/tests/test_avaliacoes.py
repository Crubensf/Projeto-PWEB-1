from datetime import date, timedelta

import pytest

ROTA = {
    "nome": "Centro → UFPI",
    "origem": "Centro",
    "destino": "UFPI",
    "hora_ida": "07:00",
    "hora_volta": "18:00",
    "vagas": 5,
    "veiculo": "Van",
    "dias_semana": ["seg", "ter", "qua", "qui", "sex", "sab", "dom"],
    "preco": 150.0,
}


def proxima_data():
    return (date.today() + timedelta(days=1)).isoformat()


def _login(client, email):
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "senha": "senha123"},
    )
    assert resp.status_code == 200, resp.text


@pytest.fixture()
def viagem_realizada(client, estudante, motorista):
    """Cria rota, faz estudante reservar, e motorista marca como realizada."""
    rota = client.post("/api/motorista/rotas", json=ROTA).json()
    client.post("/api/auth/logout")

    _login(client, "aluno@test.com")
    viagem = client.post(
        "/api/estudante/viagens",
        json={"rota_id": rota["id"], "data": proxima_data()},
    ).json()
    client.post("/api/auth/logout")

    _login(client, "motorista@test.com")
    realizada = client.put(
        f"/api/motorista/viagens/{viagem['id']}",
        json={"status": "realizada"},
    ).json()
    client.post("/api/auth/logout")

    _login(client, "aluno@test.com")
    return {"viagem": realizada, "rota": rota, "motorista_id": motorista["id"]}


def test_avaliar_viagem_realizada(client, viagem_realizada):
    resp = client.post(
        f"/api/estudante/viagens/{viagem_realizada['viagem']['id']}/avaliar",
        json={"nota": 5, "comentario": "Excelente!"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["nota"] == 5
    assert body["comentario"] == "Excelente!"


def test_avaliada_aparece_na_listagem(client, viagem_realizada):
    client.post(
        f"/api/estudante/viagens/{viagem_realizada['viagem']['id']}/avaliar",
        json={"nota": 4},
    )
    lista = client.get("/api/estudante/viagens").json()
    assert lista[0]["avaliada"] is True


def test_nao_avalia_duas_vezes(client, viagem_realizada):
    payload = {"nota": 4}
    r1 = client.post(
        f"/api/estudante/viagens/{viagem_realizada['viagem']['id']}/avaliar",
        json=payload,
    )
    assert r1.status_code == 201
    r2 = client.post(
        f"/api/estudante/viagens/{viagem_realizada['viagem']['id']}/avaliar",
        json=payload,
    )
    assert r2.status_code == 400


def test_nao_avalia_viagem_reservada(client, estudante, motorista):
    rota = client.post("/api/motorista/rotas", json=ROTA).json()
    client.post("/api/auth/logout")
    _login(client, "aluno@test.com")
    viagem = client.post(
        "/api/estudante/viagens",
        json={"rota_id": rota["id"], "data": proxima_data()},
    ).json()
    resp = client.post(
        f"/api/estudante/viagens/{viagem['id']}/avaliar",
        json={"nota": 5},
    )
    assert resp.status_code == 400


def test_nota_invalida(client, viagem_realizada):
    for nota in [0, 6, -1, 10]:
        resp = client.post(
            f"/api/estudante/viagens/{viagem_realizada['viagem']['id']}/avaliar",
            json={"nota": nota},
        )
        assert resp.status_code == 422


def test_outro_estudante_nao_avalia(client, viagem_realizada):
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
        f"/api/estudante/viagens/{viagem_realizada['viagem']['id']}/avaliar",
        json={"nota": 1},
    )
    assert resp.status_code == 404  # não enxerga viagem alheia


def test_perfil_motorista_publico_sem_avaliacoes(client, motorista):
    resp = client.get(f"/api/motoristas/{motorista['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["nome"] == motorista["nome"]
    assert body["media_avaliacoes"] is None
    assert body["total_avaliacoes"] == 0


def test_perfil_motorista_publico_com_media(client, viagem_realizada):
    client.post(
        f"/api/estudante/viagens/{viagem_realizada['viagem']['id']}/avaliar",
        json={"nota": 4},
    )
    resp = client.get(f"/api/motoristas/{viagem_realizada['motorista_id']}")
    body = resp.json()
    assert body["total_avaliacoes"] == 1
    assert body["media_avaliacoes"] == 4.0


def test_listagem_publica_de_rotas_inclui_motorista_com_media(client, viagem_realizada):
    client.post(
        f"/api/estudante/viagens/{viagem_realizada['viagem']['id']}/avaliar",
        json={"nota": 3},
    )
    client.post("/api/auth/logout")
    body = client.get("/api/rotas").json()
    assert body["total"] == 1
    assert body["items"][0]["motorista"]["media_avaliacoes"] == 3.0
    assert body["items"][0]["motorista"]["total_avaliacoes"] == 1


def test_estudante_nao_acessa_endpoint_perfil_como_motorista(client, estudante):
    # endpoint público — funciona mesmo logado como estudante
    resp = client.get("/api/motoristas/999")
    assert resp.status_code == 404
