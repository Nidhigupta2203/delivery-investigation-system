import uuid
from fastapi.testclient import TestClient


def create_test_organization(client: TestClient) -> str:
    """Helper to create an organization and return its ID."""
    suffix = uuid.uuid4().hex[:8]
    res = client.post(
        "/api/v1/organizations",
        json={"name": f"Parent Org {suffix}", "code": f"parent-org-{suffix}"},
    )
    return res.json()["id"]


def test_create_customer_success(client: TestClient):
    """Test successful customer creation under a valid organization."""
    org_id = create_test_organization(client)
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "organization_id": org_id,
        "name": "Sarah Connor",
        "email": f"sconnor_{suffix}@cyberdyne.com",
        "is_active": True,
    }
    response = client.post("/api/v1/customers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["organization_id"] == org_id
    assert "id" in data


def test_create_customer_missing_organization(client: TestClient):
    """Test that creating a customer with a non-existent organization returns 404."""
    random_org_id = str(uuid.uuid4())
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "organization_id": random_org_id,
        "name": "Ghost User",
        "email": f"ghost_{suffix}@example.com",
    }
    response = client.post("/api/v1/customers", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"].lower()


def test_create_customer_duplicate_email(client: TestClient):
    """Test that creating a customer with an existing email returns 409 Conflict."""
    org_id = create_test_organization(client)
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "organization_id": org_id,
        "name": "Duplicate User",
        "email": f"dup_{suffix}@domain.com",
    }
    res1 = client.post("/api/v1/customers", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/customers", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_create_customer_invalid_email(client: TestClient):
    """Test that invalid email format triggers 422 validation error."""
    org_id = create_test_organization(client)
    payload = {
        "organization_id": org_id,
        "name": "Invalid Email User",
        "email": "not-an-email",
    }
    response = client.post("/api/v1/customers", json=payload)
    assert response.status_code == 422


def test_get_customer_by_id(client: TestClient):
    """Test retrieving an existing customer."""
    org_id = create_test_organization(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/customers",
        json={"organization_id": org_id, "name": "Elena Rostova", "email": f"elena_{suffix}@domain.com"},
    )
    cust_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/customers/{cust_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == cust_id


def test_get_customer_not_found(client: TestClient):
    """Test that retrieving a missing customer returns 404."""
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/customers/{random_id}")
    assert response.status_code == 404


def test_list_customers_filter_by_organization(client: TestClient):
    """Test filtering customers by organization ID."""
    org_id = create_test_organization(client)
    suffix = uuid.uuid4().hex[:8]
    client.post(
        "/api/v1/customers",
        json={"organization_id": org_id, "name": "Org Customer", "email": f"org_{suffix}@domain.com"},
    )

    response = client.get(f"/api/v1/customers?organization_id={org_id}")
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)
    assert len(customers) == 1
    assert customers[0]["organization_id"] == org_id


def test_update_customer(client: TestClient):
    """Test updating a customer's name and email."""
    org_id = create_test_organization(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/customers",
        json={"organization_id": org_id, "name": "Pre-Update", "email": f"pre_{suffix}@domain.com"},
    )
    cust_id = create_res.json()["id"]

    new_email = f"post_{suffix}@domain.com"
    patch_res = client.patch(
        f"/api/v1/customers/{cust_id}",
        json={"name": "Post-Update", "email": new_email},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Post-Update"
    assert patch_res.json()["email"] == new_email


def test_delete_customer(client: TestClient):
    """Test deleting a customer returns 204 and removes entity."""
    org_id = create_test_organization(client)
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/customers",
        json={"organization_id": org_id, "name": "To Delete", "email": f"delete_{suffix}@domain.com"},
    )
    cust_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/customers/{cust_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/customers/{cust_id}")
    assert get_res.status_code == 404
