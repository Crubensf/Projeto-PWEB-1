import pytest

BASE = {
    "nome": "Rota",
    "origem": "Centro",
    "destino": "UFPI",
    "hora_ida": "07:00",
    "hora_volta": "18:00",
    "vagas": 5,
    "veiculo": "Van",
    "dias_semana": ["seg", "ter", "qua", "qui", "sex"],
    "preco": 150.0,
}


@pytest.fixture()
def varias_rotas(client, motorista):
    """3 rotas com preços e horários distintos."""
    rotas = [
        {**BASE, "nome": "Rota Cheap 06h", "preco": 80.0, "hora_ida": "06:00"},
        {**BASE, "nome": "Rota Mid 09h", "preco": 150.0, "hora_ida": "09:00"},
        {**BASE, "nome": "Rota Premium 14h", "preco": 250.0, "hora_ida": "14:00"},
    ]
    for r in rotas:
        resp = client.post("/api/motorista/rotas", json=r)
        assert resp.status_code == 200, resp.text
    return rotas


def test_busca_insensivel_a_acento(client, motorista):
    """Buscar 'jaicos' (sem acento) deve achar 'Jaicós'."""
    rota = {**BASE, "origem": "Jaicós", "destino": "São Raimundo Nonato"}
    assert client.post("/api/motorista/rotas", json=rota).status_code == 200

    # origem sem acento e em maiúscula
    assert client.get("/api/rotas?origem=jaicos").json()["total"] == 1
    assert client.get("/api/rotas?origem=JAICOS").json()["total"] == 1
    # destino sem acento
    assert client.get("/api/rotas?destino=sao raimundo").json()["total"] == 1
    # termo que não existe não acha
    assert client.get("/api/rotas?origem=teresina").json()["total"] == 0


def test_rota_retorna_chegada_estimada(client, motorista):
    """Rota com coordenadas retorna duração e chegada estimadas."""
    rota = {
        **BASE,
        "hora_ida": "06:00",
        "origem_lat": -7.3585,
        "origem_lng": -41.1376,
        "destino_lat": -7.0773,
        "destino_lng": -41.467,
    }
    body = client.post("/api/motorista/rotas", json=rota).json()
    assert body["duracao_estimada_min"] is not None
    assert body["duracao_estimada_min"] > 0
    assert body["hora_chegada_estimada"] > "06:00"  # chega depois de sair


def test_filtro_preco_min(client, varias_rotas):
    body = client.get("/api/rotas?preco_min=100").json()
    assert body["total"] == 2  # 150 e 250


def test_filtro_preco_max(client, varias_rotas):
    body = client.get("/api/rotas?preco_max=100").json()
    assert body["total"] == 1  # só 80


def test_filtro_preco_range(client, varias_rotas):
    body = client.get("/api/rotas?preco_min=100&preco_max=200").json()
    assert body["total"] == 1  # só 150


def test_filtro_hora_min(client, varias_rotas):
    body = client.get("/api/rotas?hora_min=08:00").json()
    assert body["total"] == 2  # 09:00 e 14:00


def test_filtro_hora_max(client, varias_rotas):
    body = client.get("/api/rotas?hora_max=08:00").json()
    assert body["total"] == 1  # só 06:00


def test_hora_invalida_422(client, varias_rotas):
    resp = client.get("/api/rotas?hora_min=8h")
    assert resp.status_code == 422


def test_ordenar_preco_asc(client, varias_rotas):
    body = client.get("/api/rotas?ordenar_por=preco_asc").json()
    precos = [r["preco"] for r in body["items"]]
    assert precos == [80.0, 150.0, 250.0]


def test_ordenar_preco_desc(client, varias_rotas):
    body = client.get("/api/rotas?ordenar_por=preco_desc").json()
    precos = [r["preco"] for r in body["items"]]
    assert precos == [250.0, 150.0, 80.0]


def test_ordenar_hora_asc(client, varias_rotas):
    body = client.get("/api/rotas?ordenar_por=hora_asc").json()
    horas = [r["hora_ida"] for r in body["items"]]
    assert horas == ["06:00", "09:00", "14:00"]


def test_paginacao_limit(client, varias_rotas):
    body = client.get("/api/rotas?limit=2").json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0


def test_paginacao_offset(client, varias_rotas):
    body = client.get("/api/rotas?limit=2&offset=2&ordenar_por=preco_asc").json()
    assert len(body["items"]) == 1
    assert body["items"][0]["preco"] == 250.0
    assert body["offset"] == 2


def test_limit_acima_do_max_422(client, varias_rotas):
    resp = client.get("/api/rotas?limit=999")
    assert resp.status_code == 422


def test_ordenar_invalido_422(client, varias_rotas):
    resp = client.get("/api/rotas?ordenar_por=banana")
    assert resp.status_code == 422
