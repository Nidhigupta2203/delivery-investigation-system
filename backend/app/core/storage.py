import hashlib
import io
from typing import Optional, Tuple
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageService:
    """Wrapper around Boto3 S3 client for MinIO object storage."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        """Create an S3 bucket if it does not already exist."""
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=bucket_name)
            except ClientError as exc:
                # Ignore if bucket already owned by us or created concurrently
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                    raise exc

    def ensure_default_buckets(self) -> None:
        """Ensure both source and customer default buckets exist."""
        self.ensure_bucket_exists(settings.S3_SOURCE_BUCKET)
        self.ensure_bucket_exists(settings.S3_CUSTOMER_BUCKET)

    def object_exists(self, bucket: str, key: str) -> bool:
        """Check whether an object exists in a given bucket."""
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def upload_bytes(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> Tuple[int, str]:
        """Upload in-memory bytes to S3, returning (file_size_bytes, sha256_checksum)."""
        sha256_hash = hashlib.sha256(data).hexdigest()
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return len(data), sha256_hash

    def get_object_bytes(self, bucket: str, key: str) -> bytes:
        """Retrieve the raw byte content of an S3 object."""
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def stream_and_compute_checksum(
        self,
        bucket: str,
        key: str,
        chunk_size: int = 64 * 1024,
    ) -> Tuple[int, str, bytes]:
        """Stream an object from S3, computing its size and SHA-256 hash.

        Returns (size_bytes, sha256_checksum, raw_data).
        """
        response = self.client.get_object(Bucket=bucket, Key=key)
        stream = response["Body"]
        hasher = hashlib.sha256()
        total_size = 0
        chunks = []

        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
            total_size += len(chunk)
            chunks.append(chunk)

        full_data = b"".join(chunks)
        return total_size, hasher.hexdigest(), full_data

    def transfer_and_verify(
        self,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
        expected_checksum: Optional[str] = None,
    ) -> Tuple[bool, str, int, Optional[str]]:
        """Transfer an object from source to target bucket with SHA-256 checksum verification.

        Returns:
            (success: bool, actual_checksum: str, file_size: int, error_message: Optional[str])
        """
        # 1. Verify source object exists
        if not self.object_exists(source_bucket, source_key):
            return False, "", 0, f"Source object '{source_key}' not found in bucket '{source_bucket}'."

        # 2. Ensure target bucket exists
        self.ensure_bucket_exists(target_bucket)

        # 3. Stream and compute checksum of source data
        try:
            total_size, actual_checksum, data = self.stream_and_compute_checksum(
                bucket=source_bucket,
                key=source_key,
            )
        except Exception as exc:
            return False, "", 0, f"Failed streaming source object: {str(exc)}"

        # 4. Checksum verification against manifest
        if expected_checksum and actual_checksum.lower() != expected_checksum.lower():
            return (
                False,
                actual_checksum,
                total_size,
                f"Checksum mismatch: expected '{expected_checksum}', calculated '{actual_checksum}'.",
            )

        # 5. Upload verified data to target destination
        try:
            self.client.put_object(
                Bucket=target_bucket,
                Key=target_key,
                Body=data,
            )
        except Exception as exc:
            return False, actual_checksum, total_size, f"Failed uploading to target bucket: {str(exc)}"

        return True, actual_checksum, total_size, None


# Singleton instance
storage_service = StorageService()
