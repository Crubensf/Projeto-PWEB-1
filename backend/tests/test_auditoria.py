import auditoria
from models import EventoAuditoria


def _eventos(db_session_factory_fixture=None):
    """Helper: cria sessão direta no engine de teste para inspeção."""


def test_login_falha_registra_evento(client, estudante):
    # logout primeiro
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": estudante["email"], "senha": "errada123"})

    # inspeciona via override do get_db — usa client.app.dependency_overrides
    overrides = client.app.dependency_overrides
    from db import get_db

    gen = overrides[get_db]()
    db = next(gen)
    try:
        falhas = (
            db.query(EventoAuditoria).filter(EventoAuditoria.tipo == auditoria.LOGIN_FALHA).all()
        )
        assert len(falhas) == 1
        assert falhas[0].usuario_id is None
        assert "errada123" not in (falhas[0].detalhe or "")  # senha NUNCA no log
    finally:
        gen.close()


def test_login_sucesso_registra_evento(client, estudante):
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": estudante["email"], "senha": "senha123"})

    overrides = client.app.dependency_overrides
    from db import get_db

    gen = overrides[get_db]()
    db = next(gen)
    try:
        sucessos = (
            db.query(EventoAuditoria).filter(EventoAuditoria.tipo == auditoria.LOGIN_SUCESSO).all()
        )
        # estudante fixture já fez 1 registro + 1 login automático ao logar agora
        assert len(sucessos) >= 1
        assert sucessos[-1].usuario_id == estudante["id"]
    finally:
        gen.close()


def test_registro_loga_evento(client):
    client.post(
        "/api/auth/register",
        data={
            "nome": "Novo",
            "email": "novo@test.com",
            "senha": "senha123",
            "perfil": "estudante",
        },
    )
    overrides = client.app.dependency_overrides
    from db import get_db

    gen = overrides[get_db]()
    db = next(gen)
    try:
        evs = db.query(EventoAuditoria).filter(EventoAuditoria.tipo == auditoria.REGISTRO).all()
        assert len(evs) == 1
        assert "perfil=estudante" in (evs[0].detalhe or "")
    finally:
        gen.close()


def test_criar_rota_loga_evento(client, motorista):
    client.post(
        "/api/motorista/rotas",
        json={
            "nome": "Centro → UFPI",
            "origem": "Centro",
            "destino": "UFPI",
            "hora_ida": "07:00",
            "hora_volta": "18:00",
            "vagas": 5,
            "veiculo": "Van",
            "dias_semana": ["seg", "ter", "qua", "qui", "sex"],
            "preco": 150.0,
        },
    )
    overrides = client.app.dependency_overrides
    from db import get_db

    gen = overrides[get_db]()
    db = next(gen)
    try:
        evs = db.query(EventoAuditoria).filter(EventoAuditoria.tipo == auditoria.ROTA_CRIADA).all()
        assert len(evs) == 1
        assert evs[0].usuario_id == motorista["id"]
    finally:
        gen.close()
