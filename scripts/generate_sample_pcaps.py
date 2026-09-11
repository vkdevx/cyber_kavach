import os
import sys
import time
from pathlib import Path
from scapy.all import IP, TCP, UDP, ICMP, wrpcap

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_sample_pcaps():
    pcap_dir = Path("data/pcaps")
    pcap_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating sample PCAPs in {pcap_dir}...")

    # 1. Normal Traffic PCAP (Standard HTTP/DNS packets)
    normal_pkts = []
    base_ts = time.time()
    for i in range(10):
        pkt = IP(src="192.168.1.50", dst="10.0.0.5") / TCP(sport=54320 + i, dport=80, flags="S")
        pkt.time = base_ts + (i * 0.2)
        normal_pkts.append(pkt)
    
    normal_file = pcap_dir / "normal_traffic.pcap"
    wrpcap(str(normal_file), normal_pkts)
    print(f"Created {normal_file} with {len(normal_pkts)} packets.")

    # 2. Port Scan PCAP (Single source contacting 25 distinct destination ports)
    port_scan_pkts = []
    scan_ts = time.time()
    for port in range(1, 26):
        pkt = IP(src="198.51.100.45", dst="10.0.0.5") / TCP(sport=60000, dport=port, flags="S")
        pkt.time = scan_ts + (port * 0.05)
        port_scan_pkts.append(pkt)

    port_scan_file = pcap_dir / "port_scan.pcap"
    wrpcap(str(port_scan_file), port_scan_pkts)
    print(f"Created {port_scan_file} with {len(port_scan_pkts)} packets.")

    # 3. SYN Flood PCAP (50 packets in 0.05 seconds)
    flood_pkts = []
    flood_ts = time.time()
    for i in range(50):
        pkt = IP(src="203.0.113.99", dst="10.0.0.5") / TCP(sport=50000 + i, dport=80, flags="S")
        pkt.time = flood_ts + (i * 0.001)
        flood_pkts.append(pkt)

    flood_file = pcap_dir / "syn_flood.pcap"
    wrpcap(str(flood_file), flood_pkts)
    print(f"Created {flood_file} with {len(flood_pkts)} packets.")

    print("Sample PCAP generation complete.")


if __name__ == "__main__":
    generate_sample_pcaps()
