import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.delivery import Delivery, DeliveryStatus
from app.models.recording import Recording, QualityStatus
from app.models.transfer import TransferJob, TransferJobStatus, FileTransfer, FileTransferStatus
from app.services.transfer_service import recover_stale_transfer_jobs, retry_transfer


def create_test_delivery(client: TestClient) -> tuple[str, str]:
    suffix = uuid.uuid4().hex[:8]
    org = client.post("/api/v1/organizations", json={"name": f"Org {suffix}", "code": f"rec-org-{suffix}"}).json()
    cust = client.post(
        "/api/v1/customers",
        json={"organization_id": org["id"], "name": "Recovery Customer", "email": f"rec_{suffix}@test.com"},
    ).json()
    order = client.post(
        "/api/v1/orders",
        json={"customer_id": cust["id"], "order_number": f"ORD-REC-{suffix}", "requested_recordings_count": 2},
    ).json()
    delivery = client.post(
        "/api/v1/deliveries",
        json={"order_id": order["id"], "delivery_number": f"DEL-REC-{suffix}"},
    ).json()
    return delivery["id"], suffix


def test_recover_stale_transfer_jobs(client: TestClient, db_session: Session):
    """Test that jobs stuck IN_PROGRESS (e.g. from prior worker kill) are safely marked FAILED for retry."""
    del_id, suffix = create_test_delivery(client)
    del_uuid = uuid.UUID(del_id)

    # Manually create a simulated in-progress transfer job (simulating crash)
    job = TransferJob(
        delivery_id=del_uuid,
        status=TransferJobStatus.IN_PROGRESS,
        total_files=2,
        transferred_files=1,
        total_bytes=2048,
        transferred_bytes=1024,
        retry_count=0,
    )
    db_session.add(job)
    db_session.flush()

    # File 1 completed, File 2 was in-flight when worker terminated
    ft1 = FileTransfer(
        transfer_job_id=job.id,
        recording_id=uuid.uuid4(),
        source_bucket="source-bucket",
        source_key="rec1.bin",
        target_bucket="customer-bucket",
        target_key="deliveries/DEL/rec1.bin",
        file_size_bytes=1024,
        expected_checksum="a" * 64,
        actual_checksum="a" * 64,
        status=FileTransferStatus.COMPLETED,
    )
    ft2 = FileTransfer(
        transfer_job_id=job.id,
        recording_id=uuid.uuid4(),
        source_bucket="source-bucket",
        source_key="rec2.bin",
        target_bucket="customer-bucket",
        target_key="deliveries/DEL/rec2.bin",
        file_size_bytes=1024,
        expected_checksum="b" * 64,
        status=FileTransferStatus.TRANSFERRING,
    )
    db_session.add_all([ft1, ft2])
    db_session.commit()

    # Run recovery
    recovered_count = recover_stale_transfer_jobs(db=db_session)
    assert recovered_count >= 1

    # Verify job is now marked FAILED with recovery message
    db_session.refresh(job)
    db_session.refresh(ft1)
    db_session.refresh(ft2)

    assert job.status == TransferJobStatus.FAILED
    assert "interrupted" in job.error_message.lower()
    assert ft1.status == FileTransferStatus.COMPLETED  # Preserved!
    assert ft2.status == FileTransferStatus.FAILED
    assert "worker restart" in ft2.error_message.lower()

    # Verify retry re-queues ONLY the failed file
    retried_job = retry_transfer(db=db_session, delivery_id=del_uuid)
    assert retried_job.status == TransferJobStatus.PENDING
    assert retried_job.retry_count == 1
    assert ft1.status == FileTransferStatus.COMPLETED  # Still completed!
    assert ft2.status == FileTransferStatus.PENDING    # Re-queued for retry!
