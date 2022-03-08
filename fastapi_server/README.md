# Fastapi sqlmodel webserver

## Launch local dev server

```
poetry run uvicorn fastapi_server.main:app --host localhost --port 8000 --reload
```
Now you can go to `http://0.0.0.0:8000` or `http://0.0.0.0:8000/docs` to check out the documentation to all endpoints
