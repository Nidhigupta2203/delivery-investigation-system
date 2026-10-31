import uuid
from fastapi.testclient import TestClient


def create_test_customer(client: TestClient) -> str:
    """Helper to create an organization and customer, returning customer ID."""
    suffix = uuid.uuid4().hex[:8]
    org_res = client.post(
        "/api/v1/organizations",
        json={"name": f"Org For Order {suffix}", "code": f"org-order-{suffix}"},
    )
    org_id = org_res.json()["id"]

    cust_res = client.post(
        "/api/v1/customers",
        json={"organization_id": org_id, "name": "Buyer Customer", "email": f"buyer_{suffix}@robotics.com"},
    )
    return cust_res.json()["id"]


def test_create_order_success(client: TestClient):
    """Test successful order creation with PENDING default status."""
    cust_id = create_test_customer(client)
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "customer_id": cust_id,
        "order_number": f"ORD-{suffix}",
        "requested_recordings_count": 50,
        "description": "Autonomous warehouse navigation dataset batch",
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["order_number"] == payload["order_number"]
    assert data["customer_id"] == cust_id
    assert data["status"] == "PENDING"
    assert data["requested_recordings_count"] == 50
    assert "id" in data


def test_create_order_missing_customer(client: TestClient):
    """Test that creating an order for a non-existent customer returns 404."""
    random_cust_id = str(uuid.uuid4())
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "customer_id": random_cust_id,
        "order_number": f"ORD-ERR-{suffix}",
        "requested_recordings_count": 10,
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"].lower()


def test_create_order_duplicate_order_number(client: TestClient):
    """Test that creating an order with duplicate order_number returns 409 Conflict."""
    cust_id = create_test_customer(client)
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "customer_id": cust_id,
        "order_number": f"ORD-DUP-{suffix}",
        "requested_recordings_count": 5,
    }
    res1 = client.post("/api/v1/orders", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/orders", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_create_order_negative_requested_count(client: TestClient):
    """Test that negative requested_recordings_count returns 422."""
    cust_id = create_test_customer(client)
    payload = {
        "customer_id": cust_id,
        "order_number": "ORD-NEG-001",
        "requested_recordings_count": -5,
    }
    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 422


def test_get_order_by_id(client: TestClient):
    """Test retrieving an order by ID."""
    cust_id = create_test_customer(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/orders",
        json={"customer_id": cust_id, "order_number": f"ORD-GET-{suffix}", "requested_recordings_count": 20},
    )
    order_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/orders/{order_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == order_id


def test_get_order_not_found(client: TestClient):
    """Test that retrieving a missing order returns 404."""
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/orders/{random_id}")
    assert response.status_code == 404


def test_list_orders_filter_by_status(client: TestClient):
    """Test listing orders filtered by status."""
    cust_id = create_test_customer(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/orders",
        json={"customer_id": cust_id, "order_number": f"ORD-STATUS-{suffix}", "requested_recordings_count": 10},
    )
    order_id = create_res.json()["id"]

    # Update to IN_PROGRESS
    client.patch(f"/api/v1/orders/{order_id}/status", json={"status": "IN_PROGRESS"})

    # Query filtered by IN_PROGRESS
    response = client.get("/api/v1/orders?status=IN_PROGRESS")
    assert response.status_code == 200
    orders = response.json()
    assert any(o["id"] == order_id for o in orders)


def test_update_order_status(client: TestClient):
    """Test progressing order status through lifecycle."""
    cust_id = create_test_customer(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/orders",
        json={"customer_id": cust_id, "order_number": f"ORD-FLOW-{suffix}", "requested_recordings_count": 15},
    )
    order_id = create_res.json()["id"]
    assert create_res.json()["status"] == "PENDING"

    patch_res = client.patch(f"/api/v1/orders/{order_id}/status", json={"status": "FULFILLED"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "FULFILLED"


def test_update_order_status_not_found(client: TestClient):
    """Test updating status of missing order returns 404."""
    random_id = str(uuid.uuid4())
    response = client.patch(f"/api/v1/orders/{random_id}/status", json={"status": "CANCELLED"})
    assert response.status_code == 404
