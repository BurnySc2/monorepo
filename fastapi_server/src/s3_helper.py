# DO NOT MODIFY OUTSIDE OF FASTAPI BACKEND PROJECT
import asyncio
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal, cast

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_s3.service_resource import Bucket, S3ServiceResource
from types_aiobotocore_s3.type_defs import GetObjectOutputTypeDef, HeadObjectOutputTypeDef, ObjectTypeDef

from settings import settings

# S3 error codes that mean "object/bucket missing": never retry, fail fast.
# Callers map these to None (reraise=False) or raise (reraise=True).
_NON_RETRYABLE_S3_CODES = frozenset({"404", "NoSuchKey", "NoSuchBucket", "NotFound", "NoSuchEntity"})


def _is_retryable_s3_error(exc: BaseException) -> bool:
    """Retry only retryable S3 ClientErrors (exclude 404/missing-key errors)."""
    if not isinstance(exc, ClientError):
        return False
    response = getattr(exc, "response", None)
    error = response.get("Error", {}) if isinstance(response, dict) else {}
    code = str(error.get("Code", ""))
    return code not in _NON_RETRYABLE_S3_CODES


async def ensure_bucket(bucket: str, days: int, *, raise_on_error: bool = True) -> None:
    """Ensure S3 bucket exists with CORS and expiration (idempotent)."""
    try:
        async with get_s3_client() as s3:
            try:
                await bucket_create(s3, bucket)
            except ClientError as e:
                response = getattr(e, "response", None)
                error = response.get("Error", {}) if isinstance(response, dict) else {}
                code = str(error.get("Code", ""))
                if code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                    raise
                logger.debug(f"Bucket already exists: {bucket}")
            await bucket_set_cors(s3, bucket)
            await bucket_set_expiration(s3, bucket, days)
    except ClientError as e:
        logger.warning(f"Bucket ensure failed for bucket={bucket} (S3 error): {e}")
        if raise_on_error:
            raise
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Bucket ensure failed for bucket={bucket}: {e}")
        if raise_on_error:
            raise


async def initialize_rustfs():
    await ensure_bucket(
        settings.rustfs_audiobook_bucket, settings.rustfs_audiobook_bucket_expiration_days, raise_on_error=True
    )
    await ensure_bucket(
        settings.rustfs_telegram_bucket, settings.rustfs_telegram_bucket_expiration_days, raise_on_error=True
    )


@asynccontextmanager
async def get_s3_client() -> AsyncGenerator[S3Client, None]:
    session = aioboto3.Session()
    async with session.client(  # pyrefly: ignore[no-matching-overload]
        "s3",
        endpoint_url=settings.rustfs_s3_url,
        aws_access_key_id=settings.rustfs_access_key,
        aws_secret_access_key=settings.rustfs_secret_key,
        # Make it compatible with rustfs
        config=Config(signature_version="s3v4"),
    ) as s3:
        yield cast(S3Client, s3)  # This yields the client to the endpoint and closes it automatically afterward


@asynccontextmanager
async def get_s3_resource() -> AsyncGenerator[S3ServiceResource, None]:
    session = aioboto3.Session()
    async with session.resource(
        "s3",
        endpoint_url=settings.rustfs_s3_url,
        aws_access_key_id=settings.rustfs_access_key,
        aws_secret_access_key=settings.rustfs_secret_key,
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(_is_retryable_s3_error),
    reraise=True,
)
async def _head_object_with_retry(session: S3Client, bucket: str, key: str) -> HeadObjectOutputTypeDef:
    return await session.head_object(Bucket=bucket, Key=key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(_is_retryable_s3_error),
    reraise=True,
)
async def _get_object_with_retry(session: S3Client, bucket: str, key: str) -> GetObjectOutputTypeDef:
    return await session.get_object(Bucket=bucket, Key=key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(_is_retryable_s3_error),
    reraise=True,
)
async def _delete_object_with_retry(session: S3Client, bucket: str, key: str) -> None:
    _ = await session.delete_object(Bucket=bucket, Key=key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(_is_retryable_s3_error),
    reraise=True,
)
async def _generate_presigned_url_with_retry(
    session: S3Client, bucket: str, key: str, file_name: str, expires_in_seconds: int, this_disposition: str
) -> str:
    return await session.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ResponseContentDisposition": this_disposition,
        },
        ExpiresIn=expires_in_seconds,
    )


async def object_get_info(
    session: S3Client, bucket: str, key: str, reraise: bool = False
) -> HeadObjectOutputTypeDef | None:
    """Return head metadata, or None when missing/failed and reraise is False; raise when reraise is True."""
    try:
        response = await _head_object_with_retry(session, bucket, key)
    except ClientError as e:
        logger.warning(f"S3 head_object failed for bucket={bucket} key={key}: {e}")
        if reraise:
            raise
        return None
    return response


async def object_download(session: S3Client, bucket: str, key: str, reraise: bool = False) -> bytes | None:
    """Return object bytes, or None when missing/failed and reraise is False; raise when reraise is True."""
    try:
        data = await _get_object_with_retry(session, bucket, key)
    except ClientError as e:
        logger.warning(f"S3 get_object failed for bucket={bucket} key={key}: {e}")
        if reraise:
            raise
        return None
    return await data["Body"].read()


async def object_delete(session: S3Client, bucket: str, key: str, reraise: bool = False):
    try:
        await _delete_object_with_retry(session, bucket, key)
    except ClientError as e:
        logger.warning(f"S3 delete_object failed for bucket={bucket} key={key}: {e}")
        if reraise:
            raise
        return


async def object_create_presigned_url(
    session: S3Client,
    bucket: str,
    key: str,
    file_name: str,
    expires_in_seconds: int = 3600,
    verify_object_exists: bool = False,
    disposition: Literal["attachment", "inline"] = "attachment",
    reraise: bool = False,
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

        this_disposition = "inline"
        if disposition == "attachment":
            this_disposition = f"{disposition}; filename={file_name}"
        url = await _generate_presigned_url_with_retry(
            session, bucket, key, file_name, expires_in_seconds, this_disposition
        )
    except ClientError as e:
        logger.warning(f"S3 generate_presigned_url failed for bucket={bucket} key={key}: {e}")
        if reraise:
            raise
        return None
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
        # pyrefly: ignore[bad-argument-type]
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
        await bucket_create(s3, settings.rustfs_audiobook_bucket)
        _a = await bucket_list_objects(s3, settings.rustfs_audiobook_bucket)


if __name__ == "__main__":
    asyncio.run(main())
