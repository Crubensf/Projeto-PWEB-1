ROTA_PAYLOAD = {
    "nome": "Centro → UFPI",
    "origem": "Centro",
    "destino": "UFPI",
    "hora_ida": "07:00",
    "hora_volta": "18:00",
    "vagas": 12,
    "veiculo": "Van Branca",
    "dias_semana": ["seg", "ter", "qua", "qui", "sex"],
    "preco": 150.0,
}


def test_estudante_nao_pode_criar_rota(client, estudante):
    resp = client.post("/api/motorista/rotas", json=ROTA_PAYLOAD)
    assert resp.status_code == 403


def test_motorista_cria_rota(client, motorista):
    resp = client.post("/api/motorista/rotas", json=ROTA_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["nome"] == ROTA_PAYLOAD["nome"]
    assert body["dias_semana"] == ROTA_PAYLOAD["dias_semana"]
    assert body["motorista_id"] == motorista["id"]


def test_motorista_lista_minhas_rotas(client, motorista):
    client.post("/api/motorista/rotas", json=ROTA_PAYLOAD)
    resp = client.get("/api/motorista/minhas-rotas")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_listagem_publica_de_rotas(client, motorista):
    client.post("/api/motorista/rotas", json=ROTA_PAYLOAD)
    client.cookies.clear()
    resp = client.get("/api/rotas")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_filtro_origem(client, motorista):
    client.post("/api/motorista/rotas", json=ROTA_PAYLOAD)
    resp = client.get("/api/rotas?origem=centro")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    resp_vazio = client.get("/api/rotas?origem=outro_lugar")
    body_vazio = resp_vazio.json()
    assert body_vazio["items"] == []
    assert body_vazio["total"] == 0


def test_motorista_atualiza_propria_rota(client, motorista):
    criada = client.post("/api/motorista/rotas", json=ROTA_PAYLOAD).json()
    resp = client.put(
        f"/api/motorista/rotas/{criada['id']}",
        json={"preco": 200.0},
    )
    assert resp.status_code == 200
    assert resp.json()["preco"] == 200.0


def test_motorista_deleta_propria_rota(client, motorista):
    criada = client.post("/api/motorista/rotas", json=ROTA_PAYLOAD).json()
    resp = client.delete(f"/api/motorista/rotas/{criada['id']}")
    assert resp.status_code == 204
    assert client.get("/api/motorista/minhas-rotas").json() == []


def test_rota_inexistente_404(client, motorista):
    resp = client.get("/api/motorista/rotas/9999")
    assert resp.status_code == 404


def test_validacao_hora_invalida(client, motorista):
    payload = {**ROTA_PAYLOAD, "hora_ida": "7h"}
    resp = client.post("/api/motorista/rotas", json=payload)
    assert resp.status_code == 422


def test_resumo_motorista(client, motorista):
    client.post("/api/motorista/rotas", json=ROTA_PAYLOAD)
    resp = client.get("/api/motorista/resumo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["rotas_ativas"] == 1
    assert body["viagens_hoje"] == 0


def test_rota_com_coordenadas(client, motorista):
    payload = {
        **ROTA_PAYLOAD,
        "origem_lat": -5.0892,
        "origem_lng": -42.8019,
        "destino_lat": -7.0773,
        "destino_lng": -41.4670,
    }
    resp = client.post("/api/motorista/rotas", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["origem_lat"] == -5.0892
    assert body["destino_lng"] == -41.4670


def test_coordenada_fora_do_range_422(client, motorista):
    payload = {**ROTA_PAYLOAD, "origem_lat": 95.0}  # > 90
    resp = client.post("/api/motorista/rotas", json=payload)
    assert resp.status_code == 422


def test_rota_sem_coordenadas_aceita(client, motorista):
    # Coordenadas são opcionais — payload sem elas deve continuar válido
    resp = client.post("/api/motorista/rotas", json=ROTA_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["origem_lat"] is None
    assert body["destino_lng"] is None
