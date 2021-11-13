"""
Hello world example:

- Start fastapi server
- Go to http://0.0.0.0:8000/graphql
- Enter query:

{
    hello
}
"""
import asyncio
from typing import AsyncGenerator

import strawberry
from fastapi.routing import APIRouter
from strawberry.fastapi import GraphQLRouter
from strawberry.tools import merge_types

from fastapi_server.routes.graph_ql.graphql_chat import ChatSystemMutation, ChatSystemQuery, ChatSystemSubscription

strawberry_router = APIRouter()


@strawberry.type
class RootQuery:
    @strawberry.field
    def hello(self) -> str:
        return 'Hello World'


@strawberry.type
class RootMutation:
    @strawberry.mutation
    def hello(self, some_input: str) -> str:
        return f'hello {some_input}'


@strawberry.type
class RootSubscription:
    @strawberry.subscription
    async def hello(self) -> AsyncGenerator[str, None]:
        count = 0
        while 1:
            yield f'Subscription message {count}'
            count += 1
            await asyncio.sleep(1)


Query = merge_types('Query', (RootQuery, ChatSystemQuery))
Mutation = merge_types('Mutation', (RootMutation, ChatSystemMutation))
Subscription = merge_types('Subscription', (RootSubscription, ChatSystemSubscription))

schema = strawberry.Schema(Query, mutation=Mutation, subscription=Subscription)

graphql_app = GraphQLRouter(schema)

strawberry_router.include_router(graphql_app, prefix='/graphql')
