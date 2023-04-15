from __future__ import annotations

import json
import random
from test.base_test import BaseTest

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DataObject

TODO_ITEM_REGEX = "[a-zA-Z0-9]{1,200}"


class TestTodolist(BaseTest):

    def test_add_todo_list_item_single(self):
        for i in range(2):
            with self.method_client_context() as client:
                new_todo = f"new todo text {i}"
                response = client.get("/api")
                assert response.status_code == 200
                count_before = len(response.json())

                response = client.post(f"/api/{new_todo}")
                assert response.status_code == 200

                response = client.get("/api")
                assert response.status_code == 200
                count_after = len(response.json())
                json_data = response.json()[-1]
                json_data.pop("created_timestamp")
                json_data.pop("id")
                assert json_data == {
                    "todo_text": new_todo,
                    "done_timestamp": -1.0,
                    "done": False,
                }
                assert count_after - count_before == 1

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_add_todo_list_item(self, data: DataObject):
        new_todo = data.draw(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
        with self.method_client_context() as client:
            response = client.get("/api")
            assert response.status_code == 200

            response = client.post(f"/api/{new_todo}")
            assert response.status_code == 200

            response = client.get("/api")
            assert response.status_code == 200
            json_data = response.json()[-1]
            json_data.pop("id")
            json_data.pop("created_timestamp")
            assert json_data == {
                "todo_text": new_todo,
                "done_timestamp": -1,
                "done": False,
            }

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_add_todo_list_item_with_body(self, data: DataObject):
        new_todo = data.draw(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
        with self.method_client_context() as client:
            response = client.get("/api")
            assert response.status_code == 200

            response = client.post("/api_body", data=json.dumps({"new_todo": new_todo}))
            assert response.status_code == 200

            response = client.get("/api")
            assert response.status_code == 200
            json_data = response.json()[-1]
            json_data.pop("created_timestamp")
            json_data.pop("id")
            assert json_data == {
                "todo_text": new_todo,
                "done_timestamp": -1,
                "done": False,
            }

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_add_todo_list_item_with_model(self, data: DataObject):
        new_todo = data.draw(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
        with self.method_client_context() as client:
            response = client.get("/api")
            assert response.status_code == 200

            response = client.post(
                "/api_model",
                headers={
                    "Content-Type": "application/json",
                },
                data=json.dumps({"todo_description": new_todo}),
            )
            assert response.status_code == 200

            response = client.get("/api")
            assert response.status_code == 200
            json_data = response.json()[-1]
            json_data.pop("created_timestamp")
            json_data.pop("id")
            assert json_data == {
                "todo_text": new_todo,
                "done_timestamp": -1,
                "done": False,
            }

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_remove_todo_list_items(self, data: DataObject):
        todo_items: list[str] = data.draw(
            st.lists(st.from_regex(TODO_ITEM_REGEX, fullmatch=True), min_size=1, max_size=100)
        )
        with self.method_client_context() as client:
            response = client.get("/api")
            assert response.status_code == 200
            for existing_item in response.json():
                existing_item_id = existing_item["id"]
                client.delete(f"/api/{existing_item_id}")

            response = client.get("/api")
            assert response.status_code == 200
            assert response.json() == []
            for new_todo in todo_items:
                response = client.post(
                    "/api_model",
                    headers={
                        "Content-Type": "application/json",
                    },
                    data=json.dumps({"todo_description": new_todo}),
                )
                assert response.status_code == 200

            response = client.get("/api")
            assert response.status_code == 200
            added_items = response.json()
            assert len(todo_items) == len(added_items)

            start_id = min(item["id"] for item in added_items)
            items = list(enumerate(todo_items, start=start_id))
            random.shuffle(items)
            items_amount = len(todo_items) - 1
            for item_id, _item in items:
                response = client.delete(f"/api/{item_id}")
                assert response.status_code == 200

                response = client.get("/api")
                assert response.status_code == 200
                assert items_amount == len(response.json())
                items_amount -= 1

                assert next((i for i in response.json() if i["id"] == item_id), "NOT FOUND") == "NOT FOUND"

            response = client.get("/api")
            assert response.status_code == 200
            assert len(response.json()) == 0
