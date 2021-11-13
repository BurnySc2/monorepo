from fastapi_server.routes.graphql import schema


def test_query():
    query = """
    {
        hello
    }
    """

    result = schema.execute_sync(
        query,
        variable_values={},
    )

    assert result.errors is None
    assert result.data == {
        'hello': 'Hello World',
    }
