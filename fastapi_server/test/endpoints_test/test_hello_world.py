from fastapi.testclient import TestClient

from fastapi_server.routes.hello_world import hello_world_router

client = TestClient(hello_world_router)


def test_hello_world():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'Hello': 'World'}
