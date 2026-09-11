import time
import random
import requests

API_URL = "http://localhost:8000/api/v1/telemetry/packet"

SOURCES = [
    "192.168.1.105", "198.51.100.45", "203.0.113.99",
    "198.51.100.88", "45.33.32.156", "185.220.101.5", "192.168.1.200"
]

DESTINATIONS = [
    ("10.0.0.5", 80, "TCP"),
    ("10.0.0.5", 443, "TCP"),
    ("10.0.0.5", 22, "TCP"),
    ("10.0.0.1", 53, "UDP")
]

print("Starting Continuous Live Traffic Simulator...")
print("Press Ctrl+C to stop.\n")

packet_count = 0
while True:
    src_ip = random.choice(SOURCES)
    dst_ip, dst_port, protocol = random.choice(DESTINATIONS)
    src_port = random.randint(40000, 65000)
    pkt_len = random.randint(64, 1500)
    now = time.time()

    payload = {
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": protocol,
        "packet_length": pkt_len,
        "timestamp": now,
        "tcp_flags": random.choice(["S", "PA", "A", "FA"])
    }

    try:
        res = requests.post(API_URL, json=payload, timeout=2.0)
        packet_count += 1
        if packet_count % 10 == 0:
            print(f"[{time.strftime('%H:%M:%S')}] Pushed {packet_count} live packets to Sentinel...")
    except Exception as e:
        print(f"Error pushing telemetry: {e}")

    time.sleep(0.5)
