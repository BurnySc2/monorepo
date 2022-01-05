import json
import random
from typing import List

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DataObject

from fastapi_server.test.base_test import BaseTest

TODO_ITEM_REGEX = '[a-zA-Z0-9]{1,200}'


class TestTodolist(BaseTest):

    def test_add_todo_list_item_single(self):
        new_todo = 'new todo text'
        with self.example_client_context() as client:
            response = client.get('/api')
            assert response.status_code == 200
            count_before = len(response.json())

            response = client.post(f'/api/{new_todo}')
            assert response.status_code == 200

            response = client.get('/api')
            assert response.status_code == 200
            count_after = len(response.json())
            json_data = response.json()[-1]
            json_data.pop('created_timestamp')
            assert json_data == {
                'id': 1,
                'todo_text': new_todo,
                'done_timestamp': -1,
                'done': False,
            }
            assert count_after - count_before == 1

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_add_todo_list_item(self, data: DataObject):
        new_todo = data.draw(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
        with self.example_client_context() as client:
            response = client.get('/api')
            assert response.status_code == 200
            assert response.json() == []

            response = client.post(f'/api/{new_todo}')
            assert response.status_code == 200

            response = client.get('/api')
            assert response.status_code == 200
            json_data = response.json()[0]
            json_data.pop('created_timestamp')
            assert json_data == {
                'id': 1,
                'todo_text': new_todo,
                'done_timestamp': -1,
                'done': False,
            }

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_add_todo_list_item_with_body(self, data: DataObject):
        new_todo = data.draw(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
        with self.example_client_context() as client:
            response = client.get('/api')
            assert response.status_code == 200
            assert response.json() == []

            response = client.post('/api_body', data=json.dumps({'new_todo': new_todo}))
            assert response.status_code == 200

            response = client.get('/api')
            assert response.status_code == 200
            json_data = response.json()[0]
            json_data.pop('created_timestamp')
            assert json_data == {
                'id': 1,
                'todo_text': new_todo,
                'done_timestamp': -1,
                'done': False,
            }

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_add_todo_list_item_with_model(self, data: DataObject):
        new_todo = data.draw(st.from_regex(TODO_ITEM_REGEX, fullmatch=True))
        with self.example_client_context() as client:
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
            json_data = response.json()[0]
            json_data.pop('created_timestamp')
            assert json_data == {
                'id': 1,
                'todo_text': new_todo,
                'done_timestamp': -1,
                'done': False,
            }

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_remove_todo_list_items(self, data: DataObject):
        todo_items: List[str] = data.draw(st.lists(st.from_regex(TODO_ITEM_REGEX, fullmatch=True), max_size=100))
        with self.example_client_context() as client:
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
