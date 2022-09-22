from typing import Any, Coroutine, Dict

from postgrest._async.client import AsyncPostgrestClient
from postgrest._async.request_builder import AsyncFilterRequestBuilder, AsyncRequestBuilder
from supabase.lib.client_options import ClientOptions
from supabase import Client as SyncClient


class Client(SyncClient):

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        options: ClientOptions = ClientOptions(),
    ):
        super().__init__(supabase_url=supabase_url, supabase_key=supabase_key, options=options)
        self.postgrest: AsyncPostgrestClient = self._init_postgrest_client(
            rest_url=self.rest_url,
            supabase_key=self.supabase_key,
            headers=options.headers,
            schema=options.schema,
        )

    # adapted to return AsyncRequestBuilder instead of SyncRequestBuilder
    def table(self, table_name: str) -> AsyncRequestBuilder:
        return self.from_(table_name)

    # adapted to return AsyncRequestBuilder instead of SyncRequestBuilder
    def from_(self, table_name: str) -> AsyncRequestBuilder:
        return self.postgrest.from_(table_name)

    # adapted to return AsyncFilterRequestBuilder instead of SyncFilterRequestBuilder
    def rpc(self, fn: str, params: Dict[Any, Any]) -> Coroutine[None, None, AsyncFilterRequestBuilder]:
        return self.postgrest.rpc(fn, params)

    @staticmethod
    def _init_postgrest_client(
        rest_url: str, supabase_key: str, headers: Dict[str, str], schema: str
    ) -> AsyncPostgrestClient:
        """Private helper for creating an instance of the Postgrest client."""
        client = AsyncPostgrestClient(rest_url, headers=headers, schema=schema)
        client.auth(token=supabase_key)
        return client

    #     async def remove_subscription_helper(resolve):
    #         try:
    #             await self._close_subscription(subscription)
    #             open_subscriptions = len(self.get_subscriptions())
    #             if not open_subscriptions:
    #                 error = await self.realtime.disconnect()
    #                 if error:
    #                     return {"error": None, "data": { open_subscriptions}}
    #         except Exception as e:
    #             raise e
    #     return remove_subscription_helper(subscription)

    # async def _close_subscription(self, subscription):
    #    """Close a given subscription

    #    Parameters
    #    ----------
    #    subscription
    #        The name of the channel
    #    """
    #    if not subscription.closed:
    #        await self._closeChannel(subscription)

    # def get_subscriptions(self):
    #     """Return all channels the client is subscribed to."""
    #     return self.realtime.channels

    # @staticmethod
    # def _init_realtime_client(
    #     realtime_url: str, supabase_key: str
    # ) -> SupabaseRealtimeClient:
    #     """Private method for creating an instance of the realtime-py client."""
    #     return SupabaseRealtimeClient(
    #         realtime_url, {"params": {"apikey": supabase_key}}
    #     )


def create_client(
    supabase_url: str,
    supabase_key: str,
    options: ClientOptions = ClientOptions(),
) -> Client:
    return Client(supabase_url=supabase_url, supabase_key=supabase_key, options=options)