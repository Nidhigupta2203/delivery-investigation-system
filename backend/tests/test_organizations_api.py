import uuid
from fastapi.testclient import TestClient


def test_create_organization_success(client: TestClient):
    """Test successful organization creation."""
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "name": "Boston Dynamics Robotics",
        "code": f"bd-robotics-{suffix}",
        "is_active": True,
    }
    response = client.post("/api/v1/organizations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["code"] == payload["code"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_organization_duplicate_code(client: TestClient):
    """Test that creating an organization with an existing code returns 409 Conflict."""
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "name": "Agility Robotics",
        "code": f"agility-{suffix}",
        "is_active": True,
    }
    res1 = client.post("/api/v1/organizations", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/organizations", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_create_organization_invalid_code(client: TestClient):
    """Test that invalid code formatting returns 422 Unprocessable Entity."""
    payload = {
        "name": "Invalid Org Code",
        "code": "invalid code with spaces!!",
    }
    response = client.post("/api/v1/organizations", json=payload)
    assert response.status_code == 422


def test_get_organization_by_id(client: TestClient):
    """Test retrieving an existing organization by ID."""
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/organizations",
        json={"name": "Figure AI", "code": f"figure-ai-{suffix}"},
    )
    org_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/organizations/{org_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == org_id
    assert get_res.json()["name"] == "Figure AI"


def test_get_organization_not_found(client: TestClient):
    """Test retrieving a non-existent organization returns 404."""
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/organizations/{random_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_organizations(client: TestClient):
    """Test listing organizations with pagination and filtering."""
    suffix = uuid.uuid4().hex[:8]
    client.post(
        "/api/v1/organizations",
        json={"name": f"Org List {suffix}", "code": f"org-list-{suffix}"},
    )

    response = client.get("/api/v1/organizations?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_update_organization(client: TestClient):
    """Test partially updating an organization."""
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/organizations",
        json={"name": "Original Name", "code": f"orig-{suffix}"},
    )
    org_id = create_res.json()["id"]

    update_payload = {"name": "Updated Org Name", "is_active": False}
    patch_res = client.patch(f"/api/v1/organizations/{org_id}", json=update_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "Updated Org Name"
    assert data["is_active"] is False
    assert data["code"] == f"orig-{suffix}"


def test_delete_organization(client: TestClient):
    """Test deleting an organization returns 204 and removes the entity."""
    suffix = uuid.uuid4().hex[:8]
    create_res = client.post(
        "/api/v1/organizations",
        json={"name": "To Delete Org", "code": f"delete-me-{suffix}"},
    )
    org_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/organizations/{org_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/organizations/{org_id}")
    assert get_res.status_code == 404
