# from __future__ import annotations

# from test.base_test import BaseTest
# from unittest.mock import AsyncMock, patch

# import pytest

# import routes.htmx_todolist

# class TestTodolist(BaseTest):

#     def test_access_todo(self):
#         with self.method_client_context() as client:
#             response = client.get("/todo")
#             assert response.status_code == 200
#             assert "HTMX+Fastapi Todo App" in response.text
#             assert "my_text" not in response.text

#     @pytest.mark.asyncio
#     async def test_get_todos(self):
#         with self.method_client_context() as client:  # noqa: SIM117
#             with patch.object(
#                 routes.htmx_todolist, "get_all_todos",
#                 AsyncMock(return_value=[{
#                     "id": 1,
#                     "todotext": "asd",
#                     "done": True,
#                 }])
#             ):
#                 response = client.get("/htmxapi/todo")
#                 assert response.status_code == 200

#     def test_add_todo(self):
#         with self.method_client_context() as client:  # noqa: SIM117
#             with patch.object(
#                 routes.htmx_todolist, "add_todo",
#                 AsyncMock(return_value={
#                     "id": 1,
#                     "todotext": "my_text",
#                     "done": True,
#                 })
#             ):
#                 response = client.post("/htmxapi/todo", data={"todotext": "my_text"})
#                 assert response.status_code == 200
#                 assert "my_text" in response.text
