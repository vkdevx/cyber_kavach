import os
import time
import pytest
from fastapi.testclient import TestClient

from storage.db import init_db, SessionLocal
from storage.repositories.alert_repository import AlertRepository
from storage.repositories.flow_repository import FlowRepository
from network.pcap_reader import PcapReaderService
from backend.pipeline.orchestrator import orchestrator
from backend.api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_pcap_ingestion_and_threat_detection():
    pcap_path = "data/pcaps/port_scan.pcap"
    assert os.path.exists(pcap_path), "Sample PCAP file port_scan.pcap must exist."

    # 1. Read validated packets from PCAP file
    start_time = time.time()
    packets = PcapReaderService.read_pcap(pcap_path)
    assert len(packets) == 25, "Expected 25 packets from port_scan.pcap"

    # 2. Process packets through pipeline orchestrator
    alerts_generated = []
    for pkt in packets:
        alert = orchestrator.process_packet(pkt, source="pcap")
        if alert:
            alerts_generated.append(alert)

    # Flush active flows
    expired = orchestrator.aggregator.flush_expired_flows(current_ts=time.time() + 10.0)
    for flow in expired:
        alert = orchestrator.process_flow(flow)
        if alert:
            alerts_generated.append(alert)

    end_time = time.time()
    latency = end_time - start_time

    # Latency Budget Verification (< 2.0s)
    assert latency < 2.0, f"End-to-end ingestion latency ({latency:.3f}s) exceeded 2.0s budget."

    # Verify Alert Generation & DB Persistence
    db = SessionLocal()
    alert_repo = AlertRepository(db)
    recent_alerts = alert_repo.get_recent_alerts(limit=10)
    db.close()

    assert len(recent_alerts) >= 1, "At least 1 security alert must be generated and persisted in database."
    latest = recent_alerts[0]
    assert latest.threat_category in ["Port Scanning", "Known Malicious Threat Intel Match", "Unknown Anomaly"]
    assert latest.severity in ["Medium", "High", "Critical"]
    assert latest.risk_score >= 40


def test_telemetry_rest_api_ingestion():
    # Test manual telemetry packet push via REST API
    packet_payload = {
        "src_ip": "198.51.100.45",
        "dst_ip": "10.0.0.5",
        "src_port": 54321,
        "dst_port": 80,
        "protocol": "TCP",
        "packet_length": 64,
        "timestamp": time.time(),
        "tcp_flags": "S"
    }

    response = client.post("/api/v1/telemetry/packet", json=packet_payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "success"
    assert data["processed_packets"] == 1
