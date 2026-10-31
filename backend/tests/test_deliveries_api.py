import uuid
from fastapi.testclient import TestClient


def create_test_order(client: TestClient) -> str:
    """Helper to create an organization, customer, and order, returning order ID."""
    suffix = uuid.uuid4().hex[:8]
    org_res = client.post(
        "/api/v1/organizations",
        json={"name": f"Delivery Test Org {suffix}", "code": f"del-org-{suffix}"},
    )
    org_id = org_res.json()["id"]

    cust_res = client.post(
        "/api/v1/customers",
        json={"organization_id": org_id, "name": "Delivery Customer", "email": f"del_cust_{suffix}@domain.com"},
    )
    cust_id = cust_res.json()["id"]

    order_res = client.post(
        "/api/v1/orders",
        json={"customer_id": cust_id, "order_number": f"ORD-DEL-{suffix}", "requested_recordings_count": 25},
    )
    return order_res.json()["id"]


def test_create_delivery_success(client: TestClient):
    """Test successful delivery creation with default PLANNED status."""
    order_id = create_test_order(client)
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "order_id": order_id,
        "delivery_number": f"DEL-BATCH-{suffix}",
        "source_location": "s3://source-bucket/recordings/batch_01",
        "target_location": "s3://customer-bucket/deliveries/batch_01",
    }
    response = client.post("/api/v1/deliveries", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order_id
    assert data["delivery_number"] == payload["delivery_number"]
    assert data["status"] == "PLANNED"
    assert data["accepted_at"] is None
    assert data["rejected_at"] is None
    assert "id" in data


def test_create_delivery_missing_order(client: TestClient):
    """Test that creating a delivery for a non-existent order returns 404."""
    random_order_id = str(uuid.uuid4())
    payload = {
        "order_id": random_order_id,
        "delivery_number": "DEL-GHOST-01",
    }
    response = client.post("/api/v1/deliveries", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"].lower()


def test_get_delivery_by_id(client: TestClient):
    """Test retrieving an existing delivery by ID."""
    order_id = create_test_order(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/deliveries",
        json={"order_id": order_id, "delivery_number": f"DEL-GET-{suffix}"},
    )
    del_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/deliveries/{del_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == del_id


def test_get_delivery_not_found(client: TestClient):
    """Test that retrieving a missing delivery returns 404."""
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/deliveries/{random_id}")
    assert response.status_code == 404


def test_list_deliveries_filter_by_order(client: TestClient):
    """Test listing deliveries filtered by order ID."""
    order_id = create_test_order(client)
    suffix = uuid.uuid4().hex[:8]
    client.post(
        "/api/v1/deliveries",
        json={"order_id": order_id, "delivery_number": f"DEL-LST-{suffix}"},
    )

    response = client.get(f"/api/v1/deliveries?order_id={order_id}")
    assert response.status_code == 200
    deliveries = response.json()
    assert isinstance(deliveries, list)
    assert len(deliveries) >= 1
    assert all(d["order_id"] == order_id for d in deliveries)


def test_update_delivery_status_accepted(client: TestClient):
    """Test accepting a delivery sets accepted_at timestamp automatically."""
    order_id = create_test_order(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/deliveries",
        json={"order_id": order_id, "delivery_number": f"DEL-ACCEPT-{suffix}"},
    )
    del_id = create_res.json()["id"]

    update_payload = {
        "status": "ACCEPTED",
        "decision_notes": "All recordings pass sensor calibration and timestamp sync checks.",
    }
    patch_res = client.patch(f"/api/v1/deliveries/{del_id}/status", json=update_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "ACCEPTED"
    assert data["accepted_at"] is not None
    assert data["decision_notes"] == update_payload["decision_notes"]


def test_update_delivery_status_rejected_without_reason_fails(client: TestClient):
    """Test that rejecting a delivery without a reason returns 400 Bad Request."""
    order_id = create_test_order(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/deliveries",
        json={"order_id": order_id, "delivery_number": f"DEL-REJ-ERR-{suffix}"},
    )
    del_id = create_res.json()["id"]

    # Attempt rejection without reason
    update_payload = {"status": "REJECTED"}
    patch_res = client.patch(f"/api/v1/deliveries/{del_id}/status", json=update_payload)
    assert patch_res.status_code == 400
    assert "rejection reason must be provided" in patch_res.json()["detail"].lower()


def test_update_delivery_status_rejected_with_reason(client: TestClient):
    """Test that rejecting a delivery with reason sets rejected_at and rejection_reason."""
    order_id = create_test_order(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/deliveries",
        json={"order_id": order_id, "delivery_number": f"DEL-REJ-OK-{suffix}"},
    )
    del_id = create_res.json()["id"]

    reason = "Corrupt frames detected in front camera stream between seconds 40 and 60."
    update_payload = {
        "status": "REJECTED",
        "rejection_reason": reason,
        "decision_notes": "Investigated by QA team.",
    }
    patch_res = client.patch(f"/api/v1/deliveries/{del_id}/status", json=update_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "REJECTED"
    assert data["rejected_at"] is not None
    assert data["rejection_reason"] == reason
    assert data["decision_notes"] == "Investigated by QA team."


def test_update_delivery_status_not_found(client: TestClient):
    """Test updating status of missing delivery returns 404."""
    random_id = str(uuid.uuid4())
    response = client.patch(
        f"/api/v1/deliveries/{random_id}/status",
        json={"status": "TRANSFERRING"},
    )
    assert response.status_code == 404
