# Portfolio full-stack foundation

Proyecto fullstack de aprendizaje con FastAPI, React, SQLAlchemy, Alembic y PostgreSQL.

## Ejecutar con Docker

```powershell
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

La API ejecuta `alembic upgrade head` automáticamente al iniciar.

## Consultar usuarios

```powershell
docker compose exec postgres psql -U portfolio -d portfolio -c "SELECT id, email, created_at FROM users;"
```
