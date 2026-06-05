import json
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import Settings


class S3Storage:
    def __init__(self, settings: Settings):
        if not settings.aws_region:
            raise RuntimeError("AWS_REGION is required for S3 calls")
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required for S3 calls")
        self.settings = settings
        self.client = boto3.client("s3", region_name=settings.aws_region)

    def get_json(self, key: str) -> Optional[Any]:
        try:
            response = self.client.get_object(Bucket=self.settings.s3_bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                return None
            raise
        return json.loads(response["Body"].read().decode("utf-8"))

    def put_json(self, key: str, payload: Any) -> None:
        self.client.put_object(
            Bucket=self.settings.s3_bucket,
            Key=key,
            Body=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
        )

    def get_bytes(self, key: str) -> Optional[bytes]:
        try:
            response = self.client.get_object(Bucket=self.settings.s3_bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                return None
            raise
        return response["Body"].read()

    def put_bytes(
        self,
        key: str,
        payload: bytes,
        content_type: str = "application/octet-stream",
        content_encoding: str | None = None,
    ) -> None:
        extra_args: dict[str, Any] = {
            "Bucket": self.settings.s3_bucket,
            "Key": key,
            "Body": payload,
            "ContentType": content_type,
        }
        if content_encoding:
            extra_args["ContentEncoding"] = content_encoding
        self.client.put_object(**extra_args)

    def put_text(self, key: str, text: str, content_type: str = "text/plain; charset=utf-8") -> None:
        self.client.put_object(
            Bucket=self.settings.s3_bucket,
            Key=key,
            Body=text.encode("utf-8"),
            ContentType=content_type,
        )

    def upload_file(self, local_path: str, key: str, content_type: str = "application/pdf") -> None:
        self.client.upload_file(
            local_path,
            self.settings.s3_bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    def presign_pdf(self, key: str | None) -> Optional[str]:
        if not key:
            return None
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.settings.s3_bucket, "Key": key},
            ExpiresIn=self.settings.presigned_url_ttl_seconds,
        )

    def documents_manifest(self) -> dict:
        return self.get_json(self.settings.metadata_key) or {"documents": {}}
