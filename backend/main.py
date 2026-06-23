import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from config import settings
from logging_config import get_logger, setup_logging
from routers import auth, estudante, motoristas_publico, rotas, usuarios, viagens

setup_logging()
logger = get_logger("vanja")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_url.startswith("sqlite"):
        import models  # noqa: F401 — registra os modelos
        from db import Base, engine

        Base.metadata.create_all(bind=engine)
    logger.info("app.startup", database=settings.database_url.split("@")[-1])
    yield
    logger.info("app.shutdown")


app = FastAPI(title="Van Já API", lifespan=lifespan)

# Em produção o frontend é servido pelo Apache no mesmo domínio,
# portanto /api/ não é cross-origin e o CORS não é ativado.
# A regra abaixo cobre dev local sem Docker (LAN + localhost).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"https?://(localhost|127\.0\.0\.1"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})"
        r"(:\d+)?"
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
    max_age=3600,
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Loga toda request com request_id, latência e status."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info("http.request", status=response.status_code, ms=elapsed_ms)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.exception("http.error", ms=elapsed_ms)
        raise
    finally:
        structlog.contextvars.clear_contextvars()


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"
    return response


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(rotas.public_router)
app.include_router(rotas.motorista_router)
app.include_router(viagens.router)
app.include_router(estudante.router)
app.include_router(motoristas_publico.router)


# Métricas Prometheus em /metrics — latência, contagem, status por endpoint
Instrumentator(
    should_group_status_codes=True,
    excluded_handlers=["/metrics", "/api/health"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
