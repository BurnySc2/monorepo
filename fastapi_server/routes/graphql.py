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
from typing import AsyncGenerator, Optional

import strawberry
from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session
from strawberry.fastapi import GraphQLRouter
from strawberry.tools import merge_types

from fastapi_server.helper.database import get_session
from fastapi_server.routes.graph_ql.graphql_chat import ChatSystemMutation, ChatSystemQuery, ChatSystemSubscription
from fastapi_server.routes.graph_ql.graphql_user import UserSystemMutation, UserSystemQuery

strawberry_router = APIRouter()


async def get_context(session: Session = Depends(get_session), ):
    # https://strawberry.rocks/docs/integrations/fastapi#context_getter
    return {
        'session': session,
    }


@strawberry.type
class RootQuery:

    @strawberry.field
    def hello_query(self) -> str:
        return 'Hello World'


@strawberry.type
class RootMutation:

    @strawberry.mutation
    def hello_mutation(self, some_input: Optional[str] = None) -> str:
        if some_input is None:
            some_input = 'you'
        return f'Hello {some_input}'


@strawberry.type
class RootSubscription:

    @strawberry.subscription
    async def hello_subscription(self, target: int = 100) -> AsyncGenerator[str, None]:
        count = 0
        while 1:
            yield f'Subscription message {count}'
            count += 1
            if isinstance(target, int) and count >= target:
                break
            await asyncio.sleep(1)


Query = merge_types('Query', (RootQuery, ChatSystemQuery, UserSystemQuery))
Mutation = merge_types('Mutation', (RootMutation, ChatSystemMutation, UserSystemMutation))
Subscription = merge_types('Subscription', (RootSubscription, ChatSystemSubscription))

schema = strawberry.Schema(Query, mutation=Mutation, subscription=Subscription)

graphql_app = GraphQLRouter(schema, context_getter=get_context)

strawberry_router.include_router(graphql_app, prefix='/graphql')
