import asyncio
import os
from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_s3.type_defs import HeadObjectOutputTypeDef, ListObjectsV2OutputTypeDef

ENDPOINT_URL = "http://localhost:9000"
ACCESS_KEY = os.getenv("MINIO_ACCESS_TOKEN")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY")


@asynccontextmanager
async def get_s3_client():
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    ) as s3:
        yield s3  # This yields the client to the endpoint and closes it automatically afterward


async def object_upload(session: S3Client, bucket: str, key: str, data: bytes) -> None:
    _ = await session.put_object(Bucket=bucket, Key=key, Body=data)


async def object_get_info(session: S3Client, bucket: str, key: str) -> HeadObjectOutputTypeDef | None:
    try:
        response = await session.head_object(Bucket=bucket, Key=key)
    except ClientError:
        return None
    return response


async def object_download(session: S3Client, bucket: str, key: str) -> bytes | None:
    try:
        data = await session.get_object(Bucket=bucket, Key=key)
    except ClientError:
        return None
    return data["Body"]


async def bucket_create(session: S3Client, bucket: str) -> None:
    _ = await session.create_bucket(Bucket=bucket)


async def bucket_set_expiration(session: S3Client, bucket: str, days: int) -> None:
    lifecycle_config = {"Rules": [{"ID": "ExpireAll", "Status": "Enabled", "Filter": {}, "Expiration": {"Days": days}}]}
    _ = await session.put_bucket_lifecycle_configuration(
        Bucket=bucket,
        # pyrefly: ignore
        LifecycleConfiguration=lifecycle_config,  # pyright: ignore[reportArgumentType]
    )


async def bucket_list_objects(session: S3Client, bucket: str) -> ListObjectsV2OutputTypeDef:
    objects = await session.list_objects_v2(Bucket=bucket)
    return objects


async def main():
    async with get_s3_client() as s3:
        _a = await bucket_list_objects(s3, "my-test-bucket")


if __name__ == "__main__":
    asyncio.run(main())
