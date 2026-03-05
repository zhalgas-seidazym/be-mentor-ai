# MentorAI

Backend service for MentorAI platform (FastAPI + PostgreSQL + Redis + Elasticsearch).

## Quick Start

1. Create environment file:

```bash
cp .env.example .env
```

2. Start services (example with Docker Compose):

```bash
docker-compose up -d
```

3. Run migrations:

```bash
alembic upgrade head
```

4. Start the app:

```bash
uvicorn app.main:app --reload
```

## Environment

All required variables are listed in `.env.example`.

## API Docs

FastAPI provides interactive docs:

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`

If you want static documentation in the repo, create `docs/api.md` and link it here. A common approach:

- `README.md`: quick usage + how to run.
- `docs/api.md`: endpoints, request/response examples, auth flow.

## Migrations

Create new migrations:

```bash
alembic revision -m "message"
```

Apply:

```bash
alembic upgrade head
```

## Notes

- Web search is used in OpenAI integration for learning recommendations.
- API endpoints are secured with JWT (see `/user/login` and `/user/verify-otp/register` flows).
