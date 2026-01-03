import asyncio
import os
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aioboto3
from botocore.exceptions import ClientError
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_s3.service_resource import Bucket, S3ServiceResource
from types_aiobotocore_s3.type_defs import HeadObjectOutputTypeDef, ObjectTypeDef

ENDPOINT_URL = "http://localhost:9000"
ACCESS_KEY = os.getenv("MINIO_ACCESS_TOKEN")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

# TODO Set env var
SC2_REPLAYS_BUCKET = os.getenv("DOESNT_EXIST", "sc2-replays")
AUDIOBOOK_BUCKET = os.getenv("DOESNT_EXIST", "audibooks")


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
