import time
import random
import requests
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from network.flow_models import ValidatedPacket
from backend.pipeline.orchestrator import orchestrator


def generate_benign_traffic(
    target_api_url: str = "http://localhost:8000/api/v1/telemetry/packet",
    rate_per_sec: float = 2.0,
    duration_sec: int = 10,
    direct_pipeline: bool = True
):
    """
    Generates realistic normal user traffic (HTTP GET/POST, DNS queries, simulated web browsing).
    Sends traffic directly to pipeline orchestrator or pushes to REST API endpoint.
    """
    print(f"Starting Benign Traffic Generator (Rate: {rate_per_sec} pkts/s, Duration: {duration_sec}s)...")

    # Sample benign source IP pools (Local workstation subnets)
    benign_sources = ["192.168.1.105", "192.168.1.112", "192.168.1.120"]
    # Standard service destinations (HTTP/HTTPS/DNS/NTP)
    standard_destinations = [
        ("10.0.0.5", 80, "TCP"),
        ("10.0.0.5", 443, "TCP"),
        ("10.0.0.1", 53, "UDP"),
        ("10.0.0.1", 123, "UDP")
    ]

    start_ts = time.time()
    packet_count = 0
    alerts_triggered = 0

    interval = 1.0 / max(0.1, rate_per_sec)

    while time.time() - start_ts < duration_sec:
        src_ip = random.choice(benign_sources)
        dst_ip, dst_port, protocol = random.choice(standard_destinations)
        src_port = random.randint(49152, 65535)
        pkt_len = random.randint(128, 1460)
        now = time.time()

        if direct_pipeline:
            # Send directly to pipeline orchestrator
            pkt = ValidatedPacket(
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                packet_length=pkt_len,
                timestamp=now,
                tcp_flags="A" if protocol == "TCP" else None
            )
            alert = orchestrator.process_packet(pkt, source="live")
            if alert:
                alerts_triggered += 1
        else:
            # Push payload via REST API
            payload = {
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "protocol": protocol,
                "packet_length": pkt_len,
                "timestamp": now,
                "tcp_flags": "A" if protocol == "TCP" else None
            }
            try:
                res = requests.post(target_api_url, json=payload, timeout=2.0)
                if res.status_code == 202 and res.json().get("alerts_generated_count", 0) > 0:
                    alerts_triggered += 1
            except Exception:
                pass

        packet_count += 1
        time.sleep(interval)

    # Flush active flow windows
    expired = orchestrator.aggregator.flush_expired_flows(current_ts=time.time() + 10.0)
    for flow in expired:
        alert = orchestrator.process_flow(flow)
        if alert:
            alerts_triggered += 1

    fp_rate = (alerts_triggered / max(1, packet_count)) * 100.0
    print(f"\n--- Benign Traffic Generator Summary ---")
    print(f"Total Benign Packets Emitted: {packet_count}")
    print(f"Alerts Triggered (False Positives): {alerts_triggered}")
    print(f"False Positive Rate: {fp_rate:.2f}%")

    return packet_count, alerts_triggered, fp_rate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OneWay Sentinel Normal Traffic Generator")
    parser.add_argument("--rate", type=float, default=2.0, help="Packets per second")
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")
    parser.add_argument("--api", action="store_true", help="Push via REST API endpoint instead of direct pipeline")
    args = parser.parse_args()

    generate_benign_traffic(
        rate_per_sec=args.rate,
        duration_sec=args.duration,
        direct_pipeline=not args.api
    )
