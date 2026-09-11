import time
import pytest
from fastapi.testclient import TestClient
from network.packet_validator import PacketValidator
from network.flow_models import ValidatedPacket, FlowRecord
from ml.feature_extraction import FeatureExtractor
from backend.risk.risk_engine import risk_engine
from backend.api.main import app
from storage.db import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


from ml.inference_service import InferenceService

def test_ai_inference_latency_budget():
    """Verify per-flow feature extraction, ML model inference, and risk engine scoring completes in under 10ms."""
    # Create sample flow with 20 packets
    pkts = [
        ValidatedPacket(
            src_ip="198.51.100.45",
            dst_ip="10.0.0.5",
            src_port=50000 + i,
            dst_port=80,
            protocol="TCP",
            packet_length=64,
            timestamp=1000.0 + (i * 0.01),
            tcp_flags="S"
        )
        for i in range(20)
    ]
    flow = FlowRecord(
        flow_id="flw_bench_001",
        correlation_id="corr_bench_001",
        src_ip="198.51.100.45",
        dst_ip="10.0.0.5",
        src_port=50000,
        dst_port=80,
        protocol="TCP",
        packet_count=20,
        byte_count=1280,
        start_ts=1000.0,
        end_ts=1000.19,
        source="live",
        packets=pkts
    )

    start_ts = time.perf_counter()
    features = FeatureExtractor.extract_features(flow)
    rf_class, rf_prob, if_score = InferenceService.run_inference(features)
    score, severity, confidence, category, explanation, top_features = risk_engine.evaluate_risk(
        features_dict=features,
        rf_class=rf_class,
        rf_prob=rf_prob,
        if_score=if_score
    )
    elapsed_ms = (time.perf_counter() - start_ts) * 1000.0

    print(f"\nAI Per-Flow Classification Latency (Feature Extractor + ML + Risk Engine): {elapsed_ms:.3f} ms")
    assert elapsed_ms < 50.0, f"AI classification latency {elapsed_ms:.3f}ms exceeded 50ms budget!"
    assert 0 <= score <= 100


def test_packet_validator_ip_sanitization():
    """Verify malformed and dangerous IP strings are dropped immediately."""
    bad_dict_sql = {
        "src_ip": "198.51.100.45'; DROP TABLE users; --",
        "dst_ip": "10.0.0.5",
        "src_port": 80,
        "dst_port": 80,
        "protocol": "TCP"
    }
    assert PacketValidator.validate_dict(bad_dict_sql) is None

    bad_dict_xss = {
        "src_ip": "<script>alert(1)</script>",
        "dst_ip": "10.0.0.5",
        "src_port": 80,
        "dst_port": 80,
        "protocol": "TCP"
    }
    assert PacketValidator.validate_dict(bad_dict_xss) is None

    valid_dict = {
        "src_ip": "198.51.100.45",
        "dst_ip": "10.0.0.5",
        "src_port": 8080,
        "dst_port": 80,
        "protocol": "TCP"
    }
    val = PacketValidator.validate_dict(valid_dict)
    assert val is not None
    assert val.src_ip == "198.51.100.45"


def test_telemetry_batch_size_cap():
    """Verify telemetry push route rejects batch sizes larger than 500 packets."""
    large_batch = [
        {
            "src_ip": "192.168.1.105",
            "dst_ip": "10.0.0.5",
            "src_port": 1000 + i,
            "dst_port": 80,
            "protocol": "TCP",
            "packet_length": 64
        }
        for i in range(501)
    ]
    res = client.post("/api/v1/telemetry/packet", json=large_batch)
    assert res.status_code == 413
    assert res.json()["detail"]["code"] == "BATCH_TOO_LARGE"


def test_pcap_path_traversal_defense():
    """Verify PCAP upload route sanitizes filenames and enforces extension validation."""
    fake_content = b"DUMMY_PCAP_BYTES"
    res = client.post(
        "/api/v1/pcaps/upload",
        files={"file": ("../../etc/passwd.txt", fake_content, "text/plain")}
    )
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "INVALID_FILE_TYPE"
