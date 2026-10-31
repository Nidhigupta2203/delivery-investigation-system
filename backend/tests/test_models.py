import uuid
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.models.recording import Recording, QualityStatus


def test_create_and_query_full_domain_hierarchy(db_session: Session):
    """Test creating an Organization, Customer, Order, Delivery, and Recording

    and verifying foreign key relationships and status fields.
    """
    unique_suffix = uuid.uuid4().hex[:8]

    # 1. Create Organization
    org = Organization(
        name="RoboDynamics Corp",
        code=f"robodynamics_{unique_suffix}",
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    assert org.id is not None
    assert org.created_at is not None

    # 2. Create Customer
    customer = Customer(
        organization_id=org.id,
        name="Alex Rivera",
        email=f"alex_{unique_suffix}@robodynamics.com",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    assert customer.id is not None
    assert customer.organization.name == "RoboDynamics Corp"

    # 3. Create Order
    order = Order(
        order_number=f"ORD-{unique_suffix}",
        customer_id=customer.id,
        status=OrderStatus.PENDING,
        requested_recordings_count=10,
        description="Warehouse navigation dataset batch 1",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    assert order.id is not None
    assert order.status == OrderStatus.PENDING
    assert order.customer.email == f"alex_{unique_suffix}@robodynamics.com"

    # 4. Create Delivery
    delivery = Delivery(
        delivery_number=f"DEL-{unique_suffix}-01",
        order_id=order.id,
        status=DeliveryStatus.PLANNED,
        source_location="s3://source-bucket/recordings/set_1",
        target_location="s3://customer-bucket/deliveries/set_1",
    )
    db_session.add(delivery)
    db_session.commit()
    db_session.refresh(delivery)

    assert delivery.id is not None
    assert delivery.status == DeliveryStatus.PLANNED
    assert delivery.order.order_number == f"ORD-{unique_suffix}"

    # 5. Create Recording
    recording = Recording(
        delivery_id=delivery.id,
        recording_id=f"REC-{unique_suffix}-001",
        file_name="cam_front_rgb.mp4",
        file_path="deliveries/DEL-01/cam_front_rgb.mp4",
        file_size_bytes=104857600,  # 100 MB
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        duration_seconds=124.5,
        quality_status=QualityStatus.PENDING_REVIEW,
        metadata_json={
            "resolution": "1920x1080",
            "fps": 30,
            "sensor": "Intel RealSense D435",
        },
    )
    db_session.add(recording)
    db_session.commit()
    db_session.refresh(recording)

    assert recording.id is not None
    assert recording.quality_status == QualityStatus.PENDING_REVIEW
    assert recording.delivery.delivery_number == f"DEL-{unique_suffix}-01"
    assert recording.metadata_json["fps"] == 30

    # 6. Verify reverse relationship loading
    assert len(order.deliveries) == 1
    assert order.deliveries[0].id == delivery.id
    assert len(delivery.recordings) == 1
    assert delivery.recordings[0].file_name == "cam_front_rgb.mp4"
