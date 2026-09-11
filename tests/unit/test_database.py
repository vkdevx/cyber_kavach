import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.db import Base
from storage.models_orm import FlowORM, FeatureORM, ModelResultORM, AlertORM, ThreatIntelIPORM, ThreatIntelCIDRORM
from storage.repositories.flow_repository import FlowRepository
from storage.repositories.alert_repository import AlertRepository
from storage.repositories.model_result_repository import ModelResultRepository
from storage.repositories.threat_intel_repository import ThreatIntelRepository

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_flow_repository_crud(db_session):
    repo = FlowRepository(db_session)
    flow = repo.create_flow(
        flow_id="flw_test_1",
        correlation_id="corr_test_1",
        src_ip="192.168.1.100",
        dst_ip="10.0.0.5",
        src_port=54321,
        dst_port=80,
        protocol="TCP",
        packet_count=100,
        byte_count=15000,
        start_ts=1000.0,
        end_ts=1005.0,
        source="simulator_normal"
    )
    assert flow.flow_id == "flw_test_1"
    fetched = repo.get_flow_by_id("flw_test_1")
    assert fetched is not None
    assert fetched.src_ip == "192.168.1.100"

    features = repo.create_features(
        flow_id="flw_test_1",
        total_packets=100.0,
        total_bytes=15000.0,
        avg_packet_size=150.0,
        flow_duration=5.0,
        mean_iat=0.05,
        iat_variance=0.001,
        unique_dst_ip_count=1.0,
        unique_dst_port_count=1.0,
        tcp_ratio=1.0,
        udp_ratio=0.0,
        icmp_ratio=0.0,
        small_large_pkt_ratio=0.2,
        byte_entropy=4.5
    )
    assert features.flow_id == "flw_test_1"


def test_alert_repository_crud(db_session):
    flow_repo = FlowRepository(db_session)
    flow_repo.create_flow(
        flow_id="flw_test_2",
        correlation_id="corr_test_2",
        src_ip="192.168.1.105",
        dst_ip="10.0.0.5",
        src_port=54322,
        dst_port=443,
        protocol="TCP",
        packet_count=50,
        byte_count=5000,
        start_ts=1000.0,
        end_ts=1005.0,
        source="simulator_attack"
    )

    alert_repo = AlertRepository(db_session)
    alert = alert_repo.create_alert(
        alert_id="alt_test_1",
        correlation_id="corr_test_2",
        flow_id="flw_test_2",
        risk_score=85,
        severity="Critical",
        confidence=0.92,
        threat_category="Port Scanning",
        explanation="High destination port diversity detected.",
        top_features=["unique_dst_port_count"],
        geolocation={"country": "Germany", "is_approximate": True},
        created_ts=1005.0
    )
    assert alert.alert_id == "alt_test_1"
    assert alert.status == "new"

    updated = alert_repo.update_status("alt_test_1", "acknowledged")
    assert updated.status == "acknowledged"


def test_threat_intel_repository_crud(db_session):
    repo = ThreatIntelRepository(db_session)
    record = repo.upsert_ip(
        ip="198.51.100.45",
        threat_score=85,
        category="scanner",
        source_feed="emerging_threats",
        country_code="DE",
        last_seen=1772500000.0
    )
    assert record.ip == "198.51.100.45"
    assert record.threat_score == 85

    fetched = repo.lookup_ip("198.51.100.45")
    assert fetched is not None
    assert fetched.category == "scanner"
