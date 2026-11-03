import uuid
from fastapi.testclient import TestClient

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def create_order(client: TestClient) -> str:
    suffix = uuid.uuid4().hex[:8]
    org_res = client.post(
        "/api/v1/organizations",
        json={"name": f"Comp Org {suffix}", "code": f"cmp-org-{suffix}"},
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]

    cust_res = client.post(
        "/api/v1/customers",
        json={"organization_id": org_id, "name": "Comp Customer", "email": f"cmp_{suffix}@example.com"},
    )
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]

    order_res = client.post(
        "/api/v1/orders",
        json={"customer_id": cust_id, "order_number": f"ORD-CMP-{suffix}", "requested_recordings_count": 10},
    )
    assert order_res.status_code == 201
    return order_res.json()["id"]


def create_delivery_with_manifest(client: TestClient, order_id: str, delivery_number: str, recordings: list) -> str:
    del_res = client.post(
        "/api/v1/deliveries",
        json={"order_id": order_id, "delivery_number": delivery_number},
    )
    assert del_res.status_code == 201
    delivery_id = del_res.json()["id"]

    if recordings:
        manifest_payload = {
            "manifest_version": "1.0",
            "recordings": recordings,
        }
        res = client.post(f"/api/v1/deliveries/{delivery_id}/manifest", json=manifest_payload)
        assert res.status_code == 201
    return delivery_id


def test_compare_deliveries_not_found(client: TestClient):
    """Test comparing non-existent delivery IDs returns 404."""
    order_id = create_order(client)
    del_id = create_delivery_with_manifest(client, order_id, "DEL-EXISTING", [])
    random_id = str(uuid.uuid4())

    # Base not found
    res1 = client.get(f"/api/v1/deliveries/{random_id}/compare/{del_id}")
    assert res1.status_code == 404
    assert "Base delivery" in res1.json()["detail"]

    # Target not found
    res2 = client.get(f"/api/v1/deliveries/{del_id}/compare/{random_id}")
    assert res2.status_code == 404
    assert "Target delivery" in res2.json()["detail"]


def test_compare_deliveries_identical(client: TestClient):
    """Test comparing identical deliveries reports UNCHANGED with 0 diffs."""
    order_id = create_order(client)
    recs = [
        {
            "recording_id": "REC-001",
            "file_name": "cam_front.mp4",
            "file_size_bytes": 10240,
            "checksum_sha256": HASH_A,
            "duration_seconds": 12.5,
        },
        {
            "recording_id": "REC-002",
            "file_name": "cam_rear.mp4",
            "file_size_bytes": 20480,
            "checksum_sha256": HASH_B,
            "duration_seconds": 15.0,
        },
    ]

    base_id = create_delivery_with_manifest(client, order_id, "DEL-BASE-1", recs)
    target_id = create_delivery_with_manifest(client, order_id, "DEL-TARGET-1", recs)

    res = client.get(f"/api/v1/deliveries/{base_id}/compare/{target_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["summary"]["total_base_recordings"] == 2
    assert data["summary"]["total_target_recordings"] == 2
    assert data["summary"]["unchanged_count"] == 2
    assert data["summary"]["added_count"] == 0
    assert data["summary"]["removed_count"] == 0
    assert data["summary"]["changed_count"] == 0
    assert data["summary"]["checksum_mismatches_count"] == 0
    assert data["summary"]["size_delta_bytes"] == 0

    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["diff_type"] == "UNCHANGED"
        assert len(item["diff_reasons"]) == 0
        assert item["base_recording"] is not None
        assert item["target_recording"] is not None


def test_compare_deliveries_added_removed_and_changed(client: TestClient):
    """Test comparison identifying ADDED, REMOVED, and CHANGED recordings."""
    order_id = create_order(client)

    base_recs = [
        {
            "recording_id": "REC-REMOVED",
            "file_name": "lidar_scan.bin",
            "file_size_bytes": 5000,
            "checksum_sha256": HASH_A,
        },
        {
            "recording_id": "REC-MODIFIED",
            "file_name": "front_cam.mp4",
            "file_size_bytes": 10000,
            "checksum_sha256": HASH_B,
            "duration_seconds": 10.0,
        },
    ]

    target_recs = [
        {
            "recording_id": "REC-ADDED",
            "file_name": "depth_map.png",
            "file_size_bytes": 3000,
            "checksum_sha256": HASH_C,
        },
        {
            "recording_id": "REC-MODIFIED",
            "file_name": "front_cam.mp4",
            "file_size_bytes": 12000,
            "checksum_sha256": HASH_D,  # changed checksum
            "duration_seconds": 12.0,   # changed duration
        },
    ]

    base_id = create_delivery_with_manifest(client, order_id, "DEL-BASE-DIFF", base_recs)
    target_id = create_delivery_with_manifest(client, order_id, "DEL-TARGET-DIFF", target_recs)

    res = client.get(f"/api/v1/deliveries/{base_id}/compare/{target_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["summary"]["total_base_recordings"] == 2
    assert data["summary"]["total_target_recordings"] == 2
    assert data["summary"]["added_count"] == 1
    assert data["summary"]["removed_count"] == 1
    assert data["summary"]["changed_count"] == 1
    assert data["summary"]["unchanged_count"] == 0
    assert data["summary"]["checksum_mismatches_count"] == 1
    # Size delta: target (3000 + 12000 = 15000) - base (5000 + 10000 = 15000) = 0
    assert data["summary"]["size_delta_bytes"] == 0

    items_by_id = {item["recording_id"]: item for item in data["items"]}

    # Verify ADDED item
    added_item = items_by_id["REC-ADDED"]
    assert added_item["diff_type"] == "ADDED"
    assert added_item["base_recording"] is None
    assert added_item["target_recording"]["file_name"] == "depth_map.png"

    # Verify REMOVED item
    removed_item = items_by_id["REC-REMOVED"]
    assert removed_item["diff_type"] == "REMOVED"
    assert removed_item["base_recording"]["file_name"] == "lidar_scan.bin"
    assert removed_item["target_recording"] is None

    # Verify CHANGED item
    changed_item = items_by_id["REC-MODIFIED"]
    assert changed_item["diff_type"] == "CHANGED"
    assert any("Checksum" in r for r in changed_item["diff_reasons"])
    assert any("File size" in r for r in changed_item["diff_reasons"])
    assert any("Duration" in r for r in changed_item["diff_reasons"])
