import time
from collections.abc import Callable

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse


router = APIRouter()


@router.get("/rick_morty")
async def read_users(request: Request) -> JSONResponse:
    return JSONResponse([{"username": "Rick"}, {"username": "Morty"}])


@router.get("/hello_world")
async def json_text(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "message": "Hello, World!",
        }
    )
