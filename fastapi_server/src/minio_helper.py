import asyncio
import os
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aioboto3
import httpx
from botocore.exceptions import ClientError
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_s3.service_resource import Bucket, S3ServiceResource
from types_aiobotocore_s3.type_defs import HeadObjectOutputTypeDef, ObjectTypeDef

ENDPOINT_URL = os.getenv("MINIO_URL", "http://0.0.0.0.9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_TOKEN")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

MINIO_SC2_REPLAYS_BUCKET = os.getenv("MINIO_SC2_REPLAYS_BUCKET", "sc2-replays")
MINIO_AUDIOBOOK_BUCKET = os.getenv("MINIO_AUDIOBOOK_BUCKET", "audiobooks")

GARAGE_ADMIN_URL = os.getenv("GARAGE_ADMIN_URL", "http://localhost:3903")
GARAGE_ADMIN_TOKEN = os.getenv("GARAGE_ADMIN_TOKEN", "rootroot")


class GarageInit:
    """
    Garage-specific helpers for initialization and bucket management.

    These functions are used during FastAPI startup to:
    1. Create the audiobook bucket (S3 API)
    2. Set a storage quota on the bucket (Admin API)
    3. Create an S3 access key and grant it permissions (Admin API)
    """

    @staticmethod
    async def admin_request(method: str, path: str, **kwargs) -> dict:
        """Make an authenticated request to the Garage Admin API."""
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {GARAGE_ADMIN_TOKEN}"
        headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, f"{GARAGE_ADMIN_URL}{path}", headers=headers, **kwargs)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def bucket_id(bucket_name: str) -> str | None:
        """
        Get the Garage internal UUID for a bucket by its name.

        Returns None if bucket doesn't exist or Admin API is unreachable.
        """
        try:
            data = await GarageInit.admin_request("GET", "/v2/GetBucketInfo", params={"globalAlias": bucket_name})
            return data.get("bucket", {}).get("id")
        except httpx.HTTPError:
            return None

    @staticmethod
    async def set_quota(bucket_id: str, max_size_bytes: int) -> None:
        """Set the maxSize quota (in bytes) on a bucket via Admin API."""
        await GarageInit.admin_request(
            "POST", "/v2/UpdateBucket", params={"id": bucket_id}, json={"quotas": {"maxSize": max_size_bytes}}
        )

    @staticmethod
    async def create_key(name: str) -> dict:
        """
        Create a new S3 access key via Admin API.

        Returns the key dict containing 'accessKeyId' and 'secretKey'.
        The secretKey is only shown once and cannot be recovered.
        """
        data = await GarageInit.admin_request("POST", "/v2/CreateKey", json={"name": name})
        return data["key"]

    @staticmethod
    async def allow_bucket(key_id: str, bucket_id: str) -> None:
        """Grant an S3 access key read/write/owner permissions on a bucket."""
        await GarageInit.admin_request(
            "POST",
            "/v2/AllowBucketKey",
            json={"bucket_id": bucket_id, "key_id": key_id, "read": True, "write": True, "owner": True},
        )


@asynccontextmanager
async def get_s3_client() -> AsyncGenerator[S3Client, None]:
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    ) as s3:
        yield s3  # This yields the client to the endpoint and closes it automatically afterward


@asynccontextmanager
async def get_s3_resource() -> AsyncGenerator[S3ServiceResource, None]:
    session = aioboto3.Session()
    async with session.resource(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    ) as s3:
        yield s3  # This yields the client to the endpoint and closes it automatically afterward


async def object_upload(session: S3Client, bucket: str, key: str, data: bytes) -> None:
    _ = await session.put_object(Bucket=bucket, Key=key, Body=data)


async def object_upload_async_iterable(session: S3Client, bucket: str, key: str, data: AsyncIterable[bytes]) -> None:
    """
    Pass in a async function that this function can iterate over
    async for chunk in data:
        logger.info(len(chunk))
    """

    @dataclass
    class AsyncStream:
        iterator: AsyncIterator[bytes]

        async def read(self, _size: int = -1) -> bytes:
            try:
                return await anext(self.iterator)
            except StopAsyncIteration:
                return b""

    my_stream = AsyncStream(aiter(data))

    _ = await session.upload_fileobj(Bucket=bucket, Key=key, Fileobj=my_stream)


async def object_get_info(session: S3Client, bucket: str, key: str) -> HeadObjectOutputTypeDef | None:
    try:
        response = await session.head_object(Bucket=bucket, Key=key)
    except ClientError:
        return
    return response


async def object_download(session: S3Client, bucket: str, key: str) -> bytes | None:
    try:
        data = await session.get_object(Bucket=bucket, Key=key)
    except ClientError:
        return
    return await data["Body"].read()


async def object_delete(session: S3Client, bucket: str, key: str):
    try:
        _ = await session.delete_object(Bucket=bucket, Key=key)
    except ClientError:
        return


async def object_create_presigned_url(
    session: S3Client,
    bucket: str,
    key: str,
    file_name: str,
    expires_in_seconds: int = 3600,
    verify_object_exists: bool = False,
) -> str | None:
    """
    verify_object_exists: if True, returns None if object doesn't exist
    """
    try:
        if verify_object_exists:
            obj = await object_get_info(session, bucket, key)
            if obj is None:
                return None

        url = await session.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ResponseContentDisposition": f'attachment; filename="{file_name}"',
            },
            ExpiresIn=expires_in_seconds,
        )
    except ClientError:
        return
    return url


async def bucket_create(session: S3Client, bucket: str) -> None:
    try:  # noqa: SIM105
        _ = await session.create_bucket(Bucket=bucket)
    # BucketAlreadyOwnedByYou - where to import that from?!
    except Exception:  # noqa: BLE001
        pass


async def bucket_set_expiration(session: S3Client, bucket: str, days: int) -> None:
    lifecycle_config = {"Rules": [{"ID": "ExpireAll", "Status": "Enabled", "Filter": {}, "Expiration": {"Days": days}}]}
    _ = await session.put_bucket_lifecycle_configuration(
        Bucket=bucket,
        # pyrefly: ignore
        LifecycleConfiguration=lifecycle_config,
    )


async def bucket_list_objects(session: S3Client, bucket: str, prefix: str = "") -> list[ObjectTypeDef]:
    response = await session.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=10_000)
    if "Contents" not in response:
        return []
    return response["Contents"]


async def objects_delete_with_prefix(bucket_name: str, prefix: str):
    async with get_s3_resource() as s3:
        bucket: Bucket = await s3.Bucket(bucket_name)
        _ = await bucket.objects.filter(Prefix=prefix).delete()


async def main():
    async with get_s3_client() as s3:
        _a = await bucket_list_objects(s3, "my-test-bucket")


if __name__ == "__main__":
    asyncio.run(main())
