from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

IndexRouter = APIRouter()


@IndexRouter.get("/rick_morty")
async def read_users(request: Request) -> JSONResponse:
    return JSONResponse([{"username": "Rick"}, {"username": "Morty"}])


@IndexRouter.get("/hello_world")
async def json_text(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "message": "Hello, World!",
        }
    )
