import asyncio
import os
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_s3.service_resource import Bucket, S3ServiceResource
from types_aiobotocore_s3.type_defs import HeadObjectOutputTypeDef, ObjectTypeDef

RUSTFS_S3_URL = os.getenv("RUSTFS_S3_URL", "http://0.0.0.0:9000")
RUSTFS_ACCESS_KEY = os.getenv("RUSTFS_ACCESS_KEY")
RUSTFS_SECRET_KEY = os.getenv("RUSTFS_SECRET_KEY")

RUSTFS_SC2_REPLAYS_BUCKET = os.getenv("RUSTFS_SC2_REPLAYS_BUCKET", "sc2-replays")
RUSTFS_AUDIOBOOK_BUCKET = os.getenv("RUSTFS_AUDIOBOOK_BUCKET", "rustfs-audiobook-bucket")
RUSTFS_TELEGRAM_BUCKET = os.getenv("RUSTFS_TELEGRAM_BUCKET", "rustfs-telegram-bucket")

RUSTFS_ADMIN_URL = os.getenv("RUSTFS_ADMIN_URL", "http://localhost:3903")
RUSTFS_ADMIN_TOKEN = os.getenv("RUSTFS_ADMIN_TOKEN", "rootroot")


async def initialize_rustfs():
    async with get_s3_client() as s3:
        await bucket_create(s3, RUSTFS_AUDIOBOOK_BUCKET)
        await bucket_set_cors(s3, RUSTFS_AUDIOBOOK_BUCKET)
        await bucket_set_expiration(s3, RUSTFS_AUDIOBOOK_BUCKET, days=30)
        await bucket_create(s3, RUSTFS_TELEGRAM_BUCKET)
        await bucket_set_cors(s3, RUSTFS_TELEGRAM_BUCKET)
        await bucket_set_expiration(s3, RUSTFS_TELEGRAM_BUCKET, days=90)


@asynccontextmanager
async def get_s3_client() -> AsyncGenerator[S3Client, None]:
    session = aioboto3.Session()
    async with session.client(  # pyrefly: ignore
        "s3",
        endpoint_url=RUSTFS_S3_URL,
        aws_access_key_id=RUSTFS_ACCESS_KEY,
        aws_secret_access_key=RUSTFS_SECRET_KEY,
        # Make it compatible with rustfs
        config=Config(signature_version="s3v4"),
    ) as s3:
        yield s3  # This yields the client to the endpoint and closes it automatically afterward


@asynccontextmanager
async def get_s3_resource() -> AsyncGenerator[S3ServiceResource, None]:
    session = aioboto3.Session()
    async with session.resource(
        "s3",
        endpoint_url=RUSTFS_S3_URL,
        aws_access_key_id=RUSTFS_ACCESS_KEY,
        aws_secret_access_key=RUSTFS_SECRET_KEY,
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
    disposition: str = "attachment",
) -> str | None:
    """
    verify_object_exists: if True, returns None if object doesn't exist
    disposition: "attachment" for download, "inline" for browser display
    """
    try:
        if verify_object_exists:
            obj = await object_get_info(session, bucket, key)
            if obj is None:
                return None

        safe_file_name = file_name.replace('"', '\\"')
        url = await session.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ResponseContentDisposition": f'{disposition}; filename="{safe_file_name}"',
            },
            ExpiresIn=expires_in_seconds,
        )
    except ClientError:
        return
    return url


async def bucket_create(session: S3Client, bucket: str) -> None:
    _ = await session.create_bucket(Bucket=bucket)


async def bucket_set_cors(session: S3Client, bucket: str) -> None:
    cors_config = {
        "CORSRules": [
            {
                "AllowedOrigins": ["*"],
                "AllowedMethods": ["GET"],
                "AllowedHeaders": ["*"],
                "ExposeHeaders": ["*"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }
    _ = await session.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_config)


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
        await bucket_create(s3, RUSTFS_AUDIOBOOK_BUCKET)
        _a = await bucket_list_objects(s3, RUSTFS_AUDIOBOOK_BUCKET)


if __name__ == "__main__":
    asyncio.run(main())
