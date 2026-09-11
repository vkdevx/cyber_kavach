import os
import time
import pytest
from fastapi.testclient import TestClient
from storage.db import init_db
from backend.api.main import app
from backend.api.deps import get_current_user, CurrentUser

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["zero_outbound_guarantee"] is True


def test_dashboard_stats_endpoint():
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_packets" in data
    assert "total_flows" in data
    assert "active_threat_level" in data
    assert "protocol_breakdown" in data
    assert "top_attacked_ports" in data


def test_threats_endpoints():
    response = client.get("/api/v1/threats")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_threat_intel_endpoints():
    payload = {
        "ip": "203.0.113.88",
        "threat_score": 90,
        "category": "botnet",
        "source_feed": "custom_test",
        "country_code": "RU"
    }
    add_resp = client.post("/api/v1/threat-intel/ips", json=payload)
    assert add_resp.status_code == 201
    assert add_resp.json()["ip"] == "203.0.113.88"

    lookup_resp = client.get("/api/v1/threat-intel/ips/203.0.113.88")
    assert lookup_resp.status_code == 200
    data = lookup_resp.json()
    assert data["listed"] is True
    assert data["threat_score"] == 90
    assert data["category"] == "botnet"

    list_resp = client.get("/api/v1/threat-intel/ips")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_action_block_ip_rbac_and_diode_prohibition():
    payload = {"ip": "198.51.100.45", "reason": "Analyst manual trigger"}

    # 1. Analyst user gets 403 Forbidden (RBAC Enforcement)
    resp_analyst = client.post("/api/v1/actions/block-ip", json=payload)
    assert resp_analyst.status_code == 403

    # 2. Admin user passes RBAC, but gets 400 Bad Request asserting zero-outbound diode rules
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id="usr_admin", username="admin_user", email="admin@sentinel.local", role="admin"
    )
    try:
        resp_admin = client.post("/api/v1/actions/block-ip", json=payload)
        assert resp_admin.status_code == 400
        detail = resp_admin.json()["detail"]
        assert detail["code"] == "ACTIVE_RESPONSE_PROHIBITED"
    finally:
        app.dependency_overrides.clear()


def test_geolocation_endpoint():
    response = client.get("/api/geolocation/198.51.100.45")
    assert response.status_code == 200
    data = response.json()
    assert data["ip"] == "198.51.100.45"
    assert "country" in data


def test_pcap_upload_endpoint():
    pcap_path = "data/pcaps/normal_traffic.pcap"
    assert os.path.exists(pcap_path)

    with open(pcap_path, "rb") as f:
        files = {"file": ("normal_traffic.pcap", f, "application/octet-stream")}
        response = client.post("/api/v1/pcaps/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["packets_parsed"] == 10
