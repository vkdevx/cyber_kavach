#!/usr/bin/env python3
"""
CyberKavach Attack Traffic Simulator
Generates real attack signatures for testing CyberKavach detection pipeline:
1. Nmap SYN Port Scan
2. Stealth XMAS Scan (FIN+PSH+URG)
3. Stealth NULL Scan (Flags = 0)
4. Stealth FIN Scan
5. SYN Flood / DoS Burst

Usage:
    python scripts/simulate_attack.py --type port_scan
    python scripts/simulate_attack.py --type xmas
    python scripts/simulate_attack.py --type null
    python scripts/simulate_attack.py --type syn_flood
    python scripts/simulate_attack.py --type all
"""

import sys
import time
import argparse
import requests

API_URL = "http://localhost:8000/api/v1/telemetry/packet"

def send_packet(src_ip, dst_ip, src_port, dst_port, protocol, length, flags):
    payload = {
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": protocol,
        "packet_length": length,
        "timestamp": time.time(),
        "tcp_flags": flags
    }
    try:
        requests.post(API_URL, json=payload, timeout=1.0)
    except Exception as e:
        print(f"Error: {e}")

def run_port_scan(attacker_ip="192.168.1.200", target_ip="10.0.0.5"):
    print(f"\n[⚔️ ATTACK] Simulating Nmap SYN Port Scan from {attacker_ip} -> {target_ip}...")
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 1433, 3306, 3389, 8000, 8080]
    for port in ports:
        src_port = 45000 + port
        send_packet(attacker_ip, target_ip, src_port, port, "TCP", 44, "S")
        time.sleep(0.02)
    print("   └── Sent 16 SYN probe packets across 16 ports.")

def run_xmas_scan(attacker_ip="192.168.1.201", target_ip="10.0.0.5"):
    print(f"\n[⚔️ ATTACK] Simulating Stealth XMAS Scan (FIN+PSH+URG) from {attacker_ip}...")
    ports = [22, 80, 443, 3306, 8080]
    for port in ports:
        src_port = 46000 + port
        send_packet(attacker_ip, target_ip, src_port, port, "TCP", 40, "FPU")
        time.sleep(0.03)
    print("   └── Sent XMAS probe packets (FIN+PSH+URG).")

def run_null_scan(attacker_ip="192.168.1.202", target_ip="10.0.0.5"):
    print(f"\n[⚔️ ATTACK] Simulating Stealth NULL Scan from {attacker_ip}...")
    ports = [21, 22, 80, 443, 8000]
    for port in ports:
        src_port = 47000 + port
        send_packet(attacker_ip, target_ip, src_port, port, "TCP", 40, "0")
        time.sleep(0.03)
    print("   └── Sent NULL probe packets (0 flags).")

def run_syn_flood(attacker_ip="192.168.1.203", target_ip="10.0.0.5"):
    print(f"\n[⚔️ ATTACK] Simulating SYN Flood DoS from {attacker_ip}...")
    for i in range(35):
        src_port = 50000 + i
        send_packet(attacker_ip, target_ip, src_port, 80, "TCP", 54, "S")
        time.sleep(0.005)
    print("   └── Sent 35 high-speed SYN flood packets.")

def main():
    parser = argparse.ArgumentParser(description="CyberKavach Attack Simulator")
    parser.add_argument("--type", choices=["port_scan", "xmas", "null", "syn_flood", "all"], default="all")
    parser.add_argument("--target", default="10.0.0.5")
    args = parser.parse_args()

    print("=" * 60)
    print("  🛡️  CyberKavach Attack Traffic Simulator")
    print(f"  🎯  Target: {args.target} | Test Type: {args.type.upper()}")
    print("=" * 60)

    if args.type in ["port_scan", "all"]:
        run_port_scan(target_ip=args.target)
        time.sleep(1)

    if args.type in ["xmas", "all"]:
        run_xmas_scan(target_ip=args.target)
        time.sleep(1)

    if args.type in ["null", "all"]:
        run_null_scan(target_ip=args.target)
        time.sleep(1)

    if args.type in ["syn_flood", "all"]:
        run_syn_flood(target_ip=args.target)

    print("\n✅ Simulation complete. Check your CyberKavach SOC Dashboard at http://localhost:8000!")

if __name__ == "__main__":
    main()
