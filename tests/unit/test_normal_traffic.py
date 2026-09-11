import pytest
from scripts.normal_traffic import generate_benign_traffic
from storage.db import init_db


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_normal_traffic_benign_classification():
    # Run normal traffic generator for 5 seconds at 5 pkts/sec
    packet_count, alerts_triggered, fp_rate = generate_benign_traffic(
        rate_per_sec=5.0,
        duration_sec=5,
        direct_pipeline=True
    )

    assert packet_count >= 15, "Expected at least 15 benign packets generated."
    assert alerts_triggered == 0, f"Expected 0 alerts triggered for normal traffic, got {alerts_triggered}."
    assert fp_rate == 0.0, f"Expected 0% false positive rate, got {fp_rate:.2f}%."
