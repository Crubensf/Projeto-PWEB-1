def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics_endpoint(client):
    # Dispara uma request pra alimentar métricas
    client.get("/api/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # Verifica que a métrica padrão de requisição apareceu
    assert "http_request" in body or "http_requests_total" in body
