import json
import os
import random
import unittest
from pathlib import Path
from typing import List

from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from fastapi_server.routes.todolist import set_sqlite_filename, todo_list_router

SQLITE_FILENAME = 'test.db'
set_sqlite_filename(SQLITE_FILENAME)
client: TestClient = TestClient(todo_list_router)

TODO_ITEM_REGEX = '[a-zA-Z0-9]{1,200}'


class TestHypothesis(unittest.TestCase):
    @staticmethod
    def remove_db_file():
        todos_db = Path(__file__).parents[1] / 'data' / SQLITE_FILENAME
        if todos_db.is_file():
            os.remove(todos_db)

    def setup_example(self):
        """ Called before each hypothesis test example """
        # https://github.com/HypothesisWorks/hypothesis/issues/59#issuecomment-93714824
        self.remove_db_file()

    @classmethod
    def setup_class(cls):
        """ Called before the test run """
        cls.remove_db_file()

    @classmethod
    def teardown_class(cls):
        """ Called after the test run """
        cls.remove_db_file()

    @settings(deadline=2_000)
    @given(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
    def test_add_todo_list_item(self, new_todo: str):
        response = client.get('/api')
        assert response.status_code == 200
        assert response.json() == []

        response = client.post(f'/api/{new_todo}')
        assert response.status_code == 200

        response = client.get('/api')
        assert response.status_code == 200
        assert response.json() == [{
            'content': new_todo,
            'id': 1,
        }]

    @settings(deadline=2_000)
    @given(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
    def test_add_todo_list_item_with_body(self, new_todo: str):
        response = client.get('/api')
        assert response.status_code == 200
        assert response.json() == []

        response = client.post('/api_body', data=json.dumps({'new_todo': new_todo}))
        assert response.status_code == 200

        response = client.get('/api')
        assert response.status_code == 200
        assert response.json() == [{
            'content': new_todo,
            'id': 1,
        }]

    @settings(deadline=2_000)
    @given(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
    def test_add_todo_list_item_with_model(self, new_todo: str):
        response = client.get('/api')
        assert response.status_code == 200
        assert response.json() == []

        response = client.post(
            '/api_model',
            headers={
                'Content-Type': 'application/json',
            },
            data=json.dumps({'todo_description': new_todo}),
        )
        assert response.status_code == 200

        response = client.get('/api')
        assert response.status_code == 200
        assert response.json() == [{
            'content': new_todo,
            'id': 1,
        }]

    @settings(max_examples=20, deadline=2_000)
    @given(st.lists(st.from_regex(TODO_ITEM_REGEX, fullmatch=True), max_size=100))
    def test_remove_todo_list_items(self, todo_items: List[str]):
        response = client.get('/api')
        assert response.status_code == 200
        assert response.json() == []

        for new_todo in todo_items:
            response = client.post(
                '/api_model',
                headers={
                    'Content-Type': 'application/json',
                },
                data=json.dumps({'todo_description': new_todo}),
            )
            assert response.status_code == 200

        response = client.get('/api')
        assert response.status_code == 200
        assert len(todo_items) == len(response.json())

        items = list(enumerate(todo_items, start=1))
        random.shuffle(items)
        items_amount = len(todo_items) - 1
        for item_id, _item in items:
            response = client.delete(f'/api/{item_id}')
            assert response.status_code == 200

            response = client.get('/api')
            assert response.status_code == 200
            assert items_amount == len(response.json())
            items_amount -= 1

            assert next((i for i in response.json() if i['id'] == item_id), 'NOT FOUND') == 'NOT FOUND'

        response = client.get('/api')
        assert response.status_code == 200
        assert len(response.json()) == 0
