# MentorAI

Backend service for MentorAI platform (FastAPI + PostgreSQL + Redis + Elasticsearch).

## Quick Start

1. Create environment file:

```bash
cp .env.example .env
```

2. First start (build images):

```bash
docker-compose up --build -d
```

3. Run migrations inside Docker:

```bash
docker-compose exec api alembic upgrade head
```

4. Seed reference data:

```bash
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /src/seeders/locations.sql
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /src/seeders/skills.sql
```

5. Server runs inside Docker (no separate `uvicorn` needed).

Next starts:

```bash
docker-compose up -d
```

## Environment

All required variables are listed in `.env.example`.

## API Docs

FastAPI provides interactive docs:

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`

Static documentation in the repo:

- `docs/openapi.json`: exported OpenAPI schema (if you maintain it manually).
- `docs/user-flows.md`: user flow overview.

## Migrations

Create new migrations:

```bash
docker-compose exec api alembic revision -m "message"
```

Apply:

```bash
docker-compose exec api alembic upgrade head
```

## Seeders

Reference SQL seed files live in `seeders/`.

Run after migrations:

```bash
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /src/seeders/locations.sql
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -f /src/seeders/skills.sql
```

## Notes

- Web search is used in OpenAI integration for learning recommendations.
- API endpoints are secured with JWT (see `/auth/login` and `/auth/verify-otp/register` flows).
