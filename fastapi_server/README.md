# Fastapi sqlmodel webserver

## Launch local dev server

```
poetry run uvicorn fastapi_server.main:app --host localhost --port 8000 --reload
```
Now you can go to `http://0.0.0.0:8000` or `http://0.0.0.0:8000/docs` to check out the documentation to all endpoints

## Migrations 

[How to start with alembic](https://github.com/tiangolo/sqlmodel/issues/85#issuecomment-917228849)

When changing models, you should run migrations.

To run migrations:

```
poetry run alembic revision --autogenerate -m "Initial Migration"
poetry run alembic upgrade head
```


