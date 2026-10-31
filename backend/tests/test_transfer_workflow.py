import hashlib
import uuid
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.storage import storage_service
from app.services.transfer_service import poll_and_process_pending_jobs, process_transfer_job


def setup_delivery_with_source_files(client: TestClient, file_data: dict[str, bytes]) -> tuple[str, dict[str, str]]:
    """Helper to create delivery and upload real sample files to MinIO source-bucket.

    Returns (delivery_id, {file_name: sha256_checksum}).
    """
    storage_service.ensure_default_buckets()
    suffix = uuid.uuid4().hex[:8]

    # 1. Create org, customer, order, delivery
    org = client.post("/api/v1/organizations", json={"name": f"Org {suffix}", "code": f"org-tr-{suffix}"}).json()
    cust = client.post(
        "/api/v1/customers",
        json={"organization_id": org["id"], "name": "Buyer", "email": f"buyer_{suffix}@test.com"},
    ).json()
    order = client.post(
        "/api/v1/orders",
        json={"customer_id": cust["id"], "order_number": f"ORD-TR-{suffix}", "requested_recordings_count": len(file_data)},
    ).json()
    delivery = client.post(
        "/api/v1/deliveries",
        json={"order_id": order["id"], "delivery_number": f"DEL-TR-{suffix}"},
    ).json()

    del_id = delivery["id"]

    # 2. Upload source files to MinIO source-bucket and calculate checksums
    checksum_map = {}
    manifest_recordings = []

    for file_name, content in file_data.items():
        source_key = f"recordings/{suffix}/{file_name}"
        size, sha = storage_service.upload_bytes(
            bucket=settings.S3_SOURCE_BUCKET,
            key=source_key,
            data=content,
        )
        checksum_map[file_name] = sha

        manifest_recordings.append(
            {
                "recording_id": f"REC-{file_name}",
                "file_name": file_name,
                "file_path": source_key,
                "file_size_bytes": size,
                "checksum_sha256": sha,
                "duration_seconds": 15.0,
                "metadata_json": {"sample": True},
            }
        )

    # 3. Register manifest
    client.post(
        f"/api/v1/deliveries/{del_id}/manifest",
        json={"recordings": manifest_recordings},
    )

    return del_id, checksum_map


def test_full_successful_transfer_workflow(client: TestClient):
    """Test full transfer workflow: upload to source, start transfer, verify

    checksum, check customer bucket content, and verify status updates.
    """
    sample_files = {
        "camera_front.mp4": b"RGB Camera Stream Bytes Content 2026",
        "imu_sensor.csv": b"timestamp,accel_x,accel_y,accel_z\n0.1,0.01,0.02,9.81\n",
    }
    del_id, checksum_map = setup_delivery_with_source_files(client, sample_files)

    # Start transfer job
    response = client.post(f"/api/v1/deliveries/{del_id}/transfer")
    assert response.status_code == 202
    job_data = response.json()
    job_id = job_data["id"]
    assert job_data["total_files"] == 2

    # Process job synchronously (same engine as background task)
    process_transfer_job(job_id=job_id)

    # Inspect status
    status_res = client.get(f"/api/v1/deliveries/{del_id}/transfer-status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "COMPLETED"
    assert status_data["progress_percentage"] == 100.0
    assert status_data["transferred_files"] == 2
    assert status_data["transferred_bytes"] == status_data["total_bytes"]
    assert len(status_data["file_transfers"]) == 2

    # Verify each file arrived in customer bucket with matching content
    for ft in status_data["file_transfers"]:
        assert ft["status"] == "COMPLETED"
        assert ft["actual_checksum"] == ft["expected_checksum"]
        customer_content = storage_service.get_object_bytes(ft["target_bucket"], ft["target_key"])
        assert hashlib.sha256(customer_content).hexdigest() == ft["expected_checksum"]

    # Verify delivery status is updated to TRANSFERRED
    del_res = client.get(f"/api/v1/deliveries/{del_id}")
    assert del_res.json()["status"] == "TRANSFERRED"

    # Verify recordings quality_status updated to PASSED
    manifest_res = client.get(f"/api/v1/deliveries/{del_id}/manifest")
    for r in manifest_res.json()["recordings"]:
        assert r["quality_status"] == "PASSED"


def test_transfer_checksum_mismatch_failure(client: TestClient):
    """Test that a file with corrupt expected checksum fails transfer,

    does not fulfill customer bucket, and marks status as FAILED.
    """
    suffix = uuid.uuid4().hex[:8]
    org = client.post("/api/v1/organizations", json={"name": f"Org {suffix}", "code": f"org-err-{suffix}"}).json()
    cust = client.post(
        "/api/v1/customers",
        json={"organization_id": org["id"], "name": "Buyer", "email": f"buyer_{suffix}@test.com"},
    ).json()
    order = client.post(
        "/api/v1/orders",
        json={"customer_id": cust["id"], "order_number": f"ORD-ERR-{suffix}", "requested_recordings_count": 1},
    ).json()
    delivery = client.post(
        "/api/v1/deliveries",
        json={"order_id": order["id"], "delivery_number": f"DEL-ERR-{suffix}"},
    ).json()
    del_id = delivery["id"]

    # Upload real source content
    source_content = b"Original Uncorrupted Content"
    source_key = f"recordings/{suffix}/data.bin"
    storage_service.upload_bytes(settings.S3_SOURCE_BUCKET, source_key, source_content)

    # Register manifest with wrong/corrupt expected checksum
    corrupt_sha = "1111111111111111111111111111111111111111111111111111111111111111"
    client.post(
        f"/api/v1/deliveries/{del_id}/manifest",
        json={
            "recordings": [
                {
                    "recording_id": "REC-CORRUPT",
                    "file_name": "data.bin",
                    "file_path": source_key,
                    "file_size_bytes": len(source_content),
                    "checksum_sha256": corrupt_sha,
                }
            ]
        },
    )

    # Start transfer
    transfer_res = client.post(f"/api/v1/deliveries/{del_id}/transfer")
    assert transfer_res.status_code == 202
    job_id = transfer_res.json()["id"]

    # Run processing
    process_transfer_job(job_id=job_id)

    # Verify status is FAILED
    status_res = client.get(f"/api/v1/deliveries/{del_id}/transfer-status")
    status_data = status_res.json()
    assert status_data["status"] == "FAILED"
    assert "checksum verification" in status_data["error_message"].lower()

    ft = status_data["file_transfers"][0]
    assert ft["status"] == "FAILED"
    assert "checksum mismatch" in ft["error_message"].lower()

    # Destination file MUST NOT exist in customer bucket
    assert storage_service.object_exists(ft["target_bucket"], ft["target_key"]) is False


def test_safe_retry_without_duplicate_fulfillment(client: TestClient):
    """Test retrying a failed transfer only processes failed items,

    safely preserving previously completed files without duplicate re-transfers.
    """
    storage_service.ensure_default_buckets()
    suffix = uuid.uuid4().hex[:8]

    # Setup 2 files: file1 valid, file2 initially has mismatch checksum
    content1 = b"Valid file content 1"
    content2_original = b"Original file content 2"
    sha1 = hashlib.sha256(content1).hexdigest()
    sha2_intended = hashlib.sha256(b"Fixed intended content 2").hexdigest()

    key1 = f"rec/{suffix}/file1.bin"
    key2 = f"rec/{suffix}/file2.bin"

    storage_service.upload_bytes(settings.S3_SOURCE_BUCKET, key1, content1)
    storage_service.upload_bytes(settings.S3_SOURCE_BUCKET, key2, content2_original)

    org = client.post("/api/v1/organizations", json={"name": f"Org {suffix}", "code": f"org-ret-{suffix}"}).json()
    cust = client.post(
        "/api/v1/customers",
        json={"organization_id": org["id"], "name": "Buyer", "email": f"buyer_{suffix}@test.com"},
    ).json()
    order = client.post(
        "/api/v1/orders",
        json={"customer_id": cust["id"], "order_number": f"ORD-RET-{suffix}", "requested_recordings_count": 2},
    ).json()
    delivery = client.post(
        "/api/v1/deliveries",
        json={"order_id": order["id"], "delivery_number": f"DEL-RET-{suffix}"},
    ).json()
    del_id = delivery["id"]

    client.post(
        f"/api/v1/deliveries/{del_id}/manifest",
        json={
            "recordings": [
                {"recording_id": "REC-1", "file_name": "file1.bin", "file_path": key1, "checksum_sha256": sha1},
                {"recording_id": "REC-2", "file_name": "file2.bin", "file_path": key2, "checksum_sha256": sha2_intended},
            ]
        },
    )

    # Run initial transfer
    job_id = client.post(f"/api/v1/deliveries/{del_id}/transfer").json()["id"]
    process_transfer_job(job_id=job_id)

    initial_status = client.get(f"/api/v1/deliveries/{del_id}/transfer-status").json()
    assert initial_status["status"] == "FAILED"
    assert initial_status["transferred_files"] == 1  # file1 succeeded!

    # Fix file2 in source bucket to match intended checksum
    storage_service.upload_bytes(settings.S3_SOURCE_BUCKET, key2, b"Fixed intended content 2")

    # Call retry-transfer
    retry_res = client.post(f"/api/v1/deliveries/{del_id}/retry-transfer")
    assert retry_res.status_code == 202
    assert retry_res.json()["retry_count"] == 1

    # Run worker processing on retry
    process_transfer_job(job_id=job_id)

    # Verify both files are now completed and delivery fulfilled!
    final_status = client.get(f"/api/v1/deliveries/{del_id}/transfer-status").json()
    assert final_status["status"] == "COMPLETED"
    assert final_status["transferred_files"] == 2
    assert final_status["retry_count"] == 1
    assert all(ft["status"] == "COMPLETED" for ft in final_status["file_transfers"])

    del_final = client.get(f"/api/v1/deliveries/{del_id}").json()
    assert del_final["status"] == "TRANSFERRED"
