import uuid
from fastapi.testclient import TestClient


def create_delivery_for_manifest(client: TestClient) -> str:
    """Helper to create an org, customer, order, and delivery."""
    suffix = uuid.uuid4().hex[:8]
    org = client.post("/api/v1/organizations", json={"name": f"Org {suffix}", "code": f"org-mf-{suffix}"}).json()
    cust = client.post(
        "/api/v1/customers",
        json={"organization_id": org["id"], "name": "Buyer", "email": f"buyer_{suffix}@test.com"},
    ).json()
    order = client.post(
        "/api/v1/orders",
        json={"customer_id": cust["id"], "order_number": f"ORD-MF-{suffix}", "requested_recordings_count": 10},
    ).json()
    delivery = client.post(
        "/api/v1/deliveries",
        json={"order_id": order["id"], "delivery_number": f"DEL-MF-{suffix}"},
    ).json()
    return delivery["id"]


def test_register_manifest_success(client: TestClient):
    """Test registering a valid recording manifest for a delivery."""
    del_id = create_delivery_for_manifest(client)
    payload = {
        "manifest_version": "1.0",
        "recordings": [
            {
                "recording_id": "REC-CAM-001",
                "file_name": "cam_front.mp4",
                "file_path": "recordings/batch_01/cam_front.mp4",
                "file_size_bytes": 1048576,
                "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "duration_seconds": 60.0,
                "metadata_json": {"fps": 30, "resolution": "1920x1080"},
            },
            {
                "recording_id": "REC-LIDAR-001",
                "file_name": "lidar_points.pcd",
                "file_path": "recordings/batch_01/lidar_points.pcd",
                "file_size_bytes": 2097152,
                "checksum_sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
                "duration_seconds": 60.0,
                "metadata_json": {"channels": 32, "points_per_second": 600000},
            },
        ],
    }

    response = client.post(f"/api/v1/deliveries/{del_id}/manifest", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["delivery_id"] == del_id
    assert data["total_recordings"] == 2
    assert data["total_bytes"] == 3145728
    assert len(data["recordings"]) == 2
    assert data["recordings"][0]["quality_status"] == "PENDING_REVIEW"
    assert data["recordings"][1]["metadata_json"]["channels"] == 32


def test_register_manifest_missing_delivery(client: TestClient):
    """Test registering manifest for non-existent delivery returns 404."""
    random_id = str(uuid.uuid4())
    payload = {
        "recordings": [
            {
                "recording_id": "REC-01",
                "file_name": "data.bin",
                "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            }
        ]
    }
    response = client.post(f"/api/v1/deliveries/{random_id}/manifest", json=payload)
    assert response.status_code == 404


def test_register_manifest_invalid_checksum_format(client: TestClient):
    """Test that invalid SHA-256 formatting returns 422 Unprocessable Entity."""
    del_id = create_delivery_for_manifest(client)
    payload = {
        "recordings": [
            {
                "recording_id": "REC-BAD-SHA",
                "file_name": "bad_sha.mp4",
                "checksum_sha256": "not-a-64-character-hex-hash",
            }
        ]
    }
    response = client.post(f"/api/v1/deliveries/{del_id}/manifest", json=payload)
    assert response.status_code == 422


def test_get_manifest(client: TestClient):
    """Test retrieving and inspecting the registered delivery manifest."""
    del_id = create_delivery_for_manifest(client)
    client.post(
        f"/api/v1/deliveries/{del_id}/manifest",
        json={
            "recordings": [
                {
                    "recording_id": "REC-GET-001",
                    "file_name": "nav_log.csv",
                    "file_size_bytes": 4096,
                    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                }
            ]
        },
    )

    response = client.get(f"/api/v1/deliveries/{del_id}/manifest")
    assert response.status_code == 200
    data = response.json()
    assert data["total_recordings"] == 1
    assert data["recordings"][0]["file_name"] == "nav_log.csv"
