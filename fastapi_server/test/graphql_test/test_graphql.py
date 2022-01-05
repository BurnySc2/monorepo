"""
A file for base test examples and how to use them in different ways.
"""
import hypothesis.strategies as st
import pytest
import strawberry
from hypothesis import given
from hypothesis.strategies import DataObject
from starlette.testclient import TestClient

from fastapi_server.test.base_test import BaseTest


class TestGraphql(BaseTest):

    def test_query(self, schema_fixture: strawberry.Schema):
        # https://strawberry.rocks/docs/operations/testing
        query = """
        query {
            helloQuery
        }
        """

        result = schema_fixture.execute_sync(query)

        assert result.errors is None
        assert result.data == {'helloQuery': 'Hello World'}

    @pytest.mark.asyncio
    async def test_query2(self, schema_fixture: strawberry.Schema):
        query = """
        query {
            helloQuery
        }
        """

        result = await schema_fixture.execute(query)

        assert result.errors is None
        assert result.data == {'helloQuery': 'Hello World'}

    def test_query_via_fastapi(self, method_client_fixture: TestClient):
        # See https://github.com/strawberry-graphql/strawberry/blob/main/tests/fastapi/test_query.py
        query = """
            query {
                helloQuery
            }
        """
        response = method_client_fixture.post('/graphql', json={'query': query})
        assert response.json() == {'data': {'helloQuery': 'Hello World'}}

    def test_mutation(self, schema_fixture: strawberry.Schema):
        query = """
        mutation TestMutation($someInput: String!) {
            helloMutation(someInput: $someInput)
        }
        """

        result = schema_fixture.execute_sync(query, variable_values={'someInput': 'Burny'})

        assert result.errors is None
        assert result.data == {'helloMutation': 'Hello Burny'}

    def test_mutation2(self, schema_fixture: strawberry.Schema):
        query = """
        mutation {
            helloMutation(someInput: "Burny")
        }
        """

        result = schema_fixture.execute_sync(query)

        assert result.errors is None
        assert result.data == {'helloMutation': 'Hello Burny'}

    @pytest.mark.asyncio
    async def test_mutation3(self, schema_fixture: strawberry.Schema):
        query = """
        mutation TestMutation($someInput: String!) {
            helloMutation(someInput: $someInput)
        }
        """

        result = await schema_fixture.execute(query, variable_values={'someInput': 'Burny'})

        assert result.errors is None
        assert result.data == {'helloMutation': 'Hello Burny'}

    def test_mutation_fastapi(self, method_client_fixture: TestClient):
        # See https://github.com/strawberry-graphql/strawberry/blob/main/tests/fastapi/test_query.py
        query = """
        mutation TestMutation($my_name: String!) {
            helloMutation(someInput: $my_name)
        }
        """
        response = method_client_fixture.post('/graphql', json={'query': query, 'variables': {'my_name': 'Burny'}})

        assert response.json() == {'data': {'helloMutation': 'Hello Burny'}}

    @given(data=st.data())
    def test_mutation_hypothesis(self, data: DataObject):
        some_input = data.draw(st.text())
        my_schema = BaseTest.get_schema()
        query = """
        mutation TestMutation($someInput: String!) {
            helloMutation(someInput: $someInput)
        }
        """

        result = my_schema.execute_sync(query, variable_values={'someInput': some_input})

        assert result.errors is None
        assert result.data == {'helloMutation': f'Hello {some_input}'}

    @pytest.mark.asyncio
    async def test_subscription(self, schema_fixture: strawberry.Schema):
        query = """
        subscription {
            helloSubscription(target: 3)
        }
        """

        sub = await schema_fixture.subscribe(query)

        index = 0
        async for result in sub:
            assert not result.errors
            assert result.data == {'helloSubscription': f'Subscription message {index}'}
            index += 1
