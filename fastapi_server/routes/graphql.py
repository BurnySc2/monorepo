import strawberry
from fastapi.routing import APIRouter
from strawberry.fastapi import GraphQLRouter

strawberry_router = APIRouter()
"""
Hello world example:

- Start fastapi server
- Go to http://0.0.0.0:8000/graphql
- Enter query:

{
    hello
}
"""


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return 'Hello World'


schema = strawberry.Schema(Query)

graphql_app = GraphQLRouter(schema)

strawberry_router.include_router(graphql_app, prefix='/graphql')
