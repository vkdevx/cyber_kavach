import csv
import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage.db import SessionLocal, init_db
from storage.repositories.threat_intel_repository import ThreatIntelRepository
from config.settings import settings


def seed_threat_intel():
    """
    Reads `/data/threat_intel/` CSV/JSON files (including AbuseIPDB & Tor Exit node lists)
    and seeds database threat intelligence tables.
    """
    print("Initializing database tables...")
    init_db()

    db = SessionLocal()
    repo = ThreatIntelRepository(db)
    threat_dir = Path(settings.THREAT_INTEL_DIR)

    if not threat_dir.exists():
        threat_dir.mkdir(parents=True, exist_ok=True)

    # 1. Seed malicious IPs CSV
    csv_file = threat_dir / "malicious_ips.csv"
    if csv_file.exists():
        print(f"Seeding malicious IPs from {csv_file}...")
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                repo.upsert_ip(
                    ip=row["ip"].strip(),
                    threat_score=int(row["threat_score"]),
                    category=row["category"].strip(),
                    source_feed=row["source_feed"].strip(),
                    country_code=row.get("country_code", "XX").strip(),
                    last_seen=float(row["last_seen"])
                )
        print("Malicious IPs seeded successfully.")

    # 2. Seed Tor Exit Nodes list (data/threat_intel/tor_exit_nodes.txt or json)
    tor_file = threat_dir / "tor_exit_nodes.json"
    if tor_file.exists():
        print(f"Seeding Tor exit node IPs from {tor_file}...")
        with open(tor_file, mode="r", encoding="utf-8") as f:
            tor_ips = json.load(f)
            for item in tor_ips:
                repo.upsert_ip(
                    ip=item["ip"].strip(),
                    threat_score=int(item.get("threat_score", 85)),
                    category="tor_exit_node",
                    source_feed="tor_project",
                    country_code=item.get("country_code", "XX"),
                    last_seen=time.time()
                )
        print("Tor exit nodes seeded successfully.")
    else:
        # Create default sample tor_exit_nodes.json if missing
        sample_tor = [
            {"ip": "185.220.101.5", "threat_score": 85, "country_code": "DE"},
            {"ip": "185.220.101.7", "threat_score": 85, "country_code": "DE"}
        ]
        with open(tor_file, "w", encoding="utf-8") as f:
            json.dump(sample_tor, f, indent=2)
        for item in sample_tor:
            repo.upsert_ip(
                ip=item["ip"],
                threat_score=item["threat_score"],
                category="tor_exit_node",
                source_feed="tor_project",
                country_code=item["country_code"],
                last_seen=time.time()
            )
        print("Sample Tor exit nodes generated and seeded successfully.")

    # 3. Seed CIDR Blacklists JSON
    cidr_file = threat_dir / "malicious_cidrs.json"
    if cidr_file.exists():
        print(f"Seeding CIDR blacklists from {cidr_file}...")
        with open(cidr_file, mode="r", encoding="utf-8") as f:
            cidrs = json.load(f)
            for item in cidrs:
                repo.upsert_cidr(
                    cidr_id=item["cidr_id"],
                    cidr_block=item["cidr_block"],
                    threat_score=int(item["threat_score"]),
                    category=item["category"],
                    source_feed=item["source_feed"],
                    created_ts=float(item["created_ts"])
                )
        print("Malicious CIDRs seeded successfully.")

    # 4. Seed Reputation Feeds / AbuseIPDB List JSON
    rep_file = threat_dir / "reputation_feeds.json"
    if rep_file.exists():
        print(f"Seeding reputation feeds from {rep_file}...")
        with open(rep_file, mode="r", encoding="utf-8") as f:
            feeds = json.load(f)
            for item in feeds:
                repo.upsert_ip(
                    ip=item["ip"].strip(),
                    threat_score=int(item["threat_score"]),
                    category=item["category"].strip(),
                    source_feed=item["source_feed"].strip(),
                    country_code=item.get("country_code", "XX").strip(),
                    last_seen=float(item["last_seen"])
                )
        print("Reputation feeds seeded successfully.")

    db.close()
    print("Database threat intelligence seeding completed successfully.")


if __name__ == "__main__":
    seed_threat_intel()
