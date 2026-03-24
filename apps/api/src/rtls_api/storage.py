from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from rtls_api.config import Settings


@dataclass
class StoredObject:
    content: bytes
    content_type: str


class ObjectStorageService:
    def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
        raise NotImplementedError

    def get_object(self, *, key: str) -> StoredObject:
        raise NotImplementedError

    def delete_object(self, *, key: str) -> None:
        raise NotImplementedError


class LocalObjectStorageService(ObjectStorageService):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / key

    def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
        del content_type
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def get_object(self, *, key: str) -> StoredObject:
        path = self._path(key)
        return StoredObject(
            content=path.read_bytes(),
            content_type=_guess_content_type(path.suffix),
        )

    def delete_object(self, *, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()


class S3CompatibleObjectStorageService(ObjectStorageService):
    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.object_storage_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.object_storage_endpoint,
            aws_access_key_id=settings.object_storage_access_key,
            aws_secret_access_key=settings.object_storage_secret_key,
            region_name=settings.object_storage_region,
            config=Config(s3={"addressing_style": "path"}),
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return
        except ClientError:
            pass

        create_kwargs = {"Bucket": self.bucket}
        if self.client.meta.region_name and self.client.meta.region_name != "us-east-1":
            create_kwargs["CreateBucketConfiguration"] = {
                "LocationConstraint": self.client.meta.region_name
            }
        self.client.create_bucket(**create_kwargs)

    def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    def get_object(self, *, key: str) -> StoredObject:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        content_type = response.get("ContentType") or "application/octet-stream"
        return StoredObject(content=response["Body"].read(), content_type=content_type)

    def delete_object(self, *, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def create_object_storage_service(settings: Settings) -> ObjectStorageService:
    if settings.object_storage_endpoint.startswith("file://"):
        parsed = urlparse(settings.object_storage_endpoint)
        return LocalObjectStorageService(Path(parsed.path))

    return S3CompatibleObjectStorageService(settings)


def _guess_content_type(suffix: str) -> str:
    extension = suffix.lower()
    if extension == ".png":
        return "image/png"
    if extension in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return "application/octet-stream"
