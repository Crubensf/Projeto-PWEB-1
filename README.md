# Van Já

Sistema de cadastro e busca de rotas de van universitária. Backend em FastAPI,
frontend HTML/CSS/JS estático servido por Apache em produção.

## Stack

- **Backend**: FastAPI + SQLAlchemy + Pydantic + JWT (cookie HttpOnly)
- **Banco**: PostgreSQL 16 (Docker) — fallback SQLite em dev local sem Docker
- **Frontend**: HTML/CSS/JS vanilla
- **Servidor estático/proxy**: Apache httpd 2.4 com SSL self-signed

## Subir com Docker

Pré-requisitos: Docker + Docker Compose.

```bash
cp .env.example .env
# edite o .env e troque POSTGRES_PASSWORD e SECRET_KEY
docker compose up --build
```

Acessar em `https://localhost` (o certificado é self-signed — aceite o aviso
do navegador). O HTTP em `:80` redireciona para HTTPS automaticamente.

Parar:

```bash
docker compose down
```

Resetar o banco (apaga o volume):

```bash
docker compose down -v
```

## Rodar testes

```bash
cd backend
pip install -r requirements.txt
pytest
```

A suite usa SQLite em memória — não exige Docker nem Postgres rodando.

## Migrations (Alembic)

Em Docker, o entrypoint do backend já roda `alembic upgrade head` antes do uvicorn.
Para criar uma nova revisão após alterar [models.py](backend/models.py):

```bash
cd backend
alembic revision --autogenerate -m "descricao da mudanca"
alembic upgrade head    # aplica localmente
```

Em SQLite local sem Alembic, o `lifespan` em [main.py](backend/main.py) cria
as tabelas automaticamente na subida.

## Dev local sem Docker

```bash
python start.py
```

Sobe o backend (uvicorn) na 8000 e um servidor estático na 5500.
Nesse modo o `frontend/js/utils.js` precisa ter `API_BASE` apontando
para `http://localhost:8000`.

## Estrutura

```
backend/         # FastAPI app (main, models, schemas, db)
backend/tests/   # pytest suite
frontend/        # HTML/CSS/JS estático + httpd.conf
docker-compose.yml
.env.example
```
