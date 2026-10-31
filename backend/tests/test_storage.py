import hashlib
import uuid
from app.core.config import settings
from app.core.storage import storage_service


def test_storage_service_buckets_and_upload():
    """Test ensuring default buckets and uploading raw bytes with SHA-256 calculation."""
    storage_service.ensure_default_buckets()

    assert storage_service.object_exists(settings.S3_SOURCE_BUCKET, "non_existent_key.bin") is False

    content = b"Robotics LiDAR sample data 2026-10-31"
    expected_sha = hashlib.sha256(content).hexdigest()
    key = f"test_lidar_{uuid.uuid4().hex[:8]}.bin"

    size, actual_sha = storage_service.upload_bytes(
        bucket=settings.S3_SOURCE_BUCKET,
        key=key,
        data=content,
    )
    assert size == len(content)
    assert actual_sha == expected_sha
    assert storage_service.object_exists(settings.S3_SOURCE_BUCKET, key) is True


def test_transfer_and_verify_success():
    """Test streaming transfer with valid checksum match."""
    storage_service.ensure_default_buckets()

    content = b"Camera RGB Stream Chunk #1"
    sha = hashlib.sha256(content).hexdigest()
    source_key = f"source_stream_{uuid.uuid4().hex[:8]}.mp4"
    target_key = f"target_stream_{uuid.uuid4().hex[:8]}.mp4"

    # Upload to source bucket
    storage_service.upload_bytes(settings.S3_SOURCE_BUCKET, source_key, content)

    # Transfer with matching checksum
    success, actual_sha, size, err = storage_service.transfer_and_verify(
        source_bucket=settings.S3_SOURCE_BUCKET,
        source_key=source_key,
        target_bucket=settings.S3_CUSTOMER_BUCKET,
        target_key=target_key,
        expected_checksum=sha,
    )

    assert success is True
    assert actual_sha == sha
    assert size == len(content)
    assert err is None
    assert storage_service.object_exists(settings.S3_CUSTOMER_BUCKET, target_key) is True

    # Verify content in customer bucket
    copied_content = storage_service.get_object_bytes(settings.S3_CUSTOMER_BUCKET, target_key)
    assert copied_content == content


def test_transfer_and_verify_checksum_mismatch():
    """Test that transfer fails and does not fulfill destination when checksum mismatches."""
    storage_service.ensure_default_buckets()

    content = b"Uncorrupted actual source bytes"
    actual_sha = hashlib.sha256(content).hexdigest()
    corrupt_expected_sha = "0000000000000000000000000000000000000000000000000000000000000000"

    source_key = f"corrupt_test_{uuid.uuid4().hex[:8]}.bin"
    target_key = f"should_not_exist_{uuid.uuid4().hex[:8]}.bin"

    storage_service.upload_bytes(settings.S3_SOURCE_BUCKET, source_key, content)

    success, computed_sha, size, err = storage_service.transfer_and_verify(
        source_bucket=settings.S3_SOURCE_BUCKET,
        source_key=source_key,
        target_bucket=settings.S3_CUSTOMER_BUCKET,
        target_key=target_key,
        expected_checksum=corrupt_expected_sha,
    )

    assert success is False
    assert computed_sha == actual_sha
    assert err is not None
    assert "checksum mismatch" in err.lower()
    # File must NOT be created in target customer bucket
    assert storage_service.object_exists(settings.S3_CUSTOMER_BUCKET, target_key) is False
