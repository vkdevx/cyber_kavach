# OneWay Sentinel — Threat Intelligence & Reputation Specification (`threat-intel.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`architecture.md:359`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md#L359) and [`rules.md:418`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L418).

---

## 1. Threat Intelligence Overview

OneWay Sentinel integrates offline, local threat intelligence feeds to enrich traffic telemetry and augment ML detection scores. Because the system operates behind a strict data diode without external internet access, all threat intelligence feeds, IP reputation databases, CIDR blacklists, and Geolocation databases are stored locally inside `/data/threat_intel/` and loaded into indexed SQLite lookup tables at startup.

---

## 2. Threat Intel Data Sources (`/data/threat_intel/`)

| File Path | Format | Description | Target Database Table |
|---|---|---|---|
| `/data/threat_intel/malicious_ips.csv` | CSV | Historical attacking IPs, threat scores (0-100), categories, and feed names. | `threat_intel_ips` |
| `/data/threat_intel/malicious_cidrs.json` | JSON | Known malicious subnet blocks (CIDRs) associated with command-and-control or scanning infrastructure. | `threat_intel_cidrs` |
| `/data/threat_intel/reputation_feeds.json` | JSON | Composite IP reputation scores and historical attack metadata. | `threat_intel_ips` |
| `/data/threat_intel/GeoLite2-City.mmdb` | Binary | MaxMind GeoLite2 City binary database for offline IP-to-Country/City lookups. | Read directly via `geoip2` library. |

---

## 3. Data Loading & Indexing Architecture

At application startup, `backend/pipeline/orchestrator.py` invokes `storage/repositories/threat_intel_repository.py` to seed and update the local SQLite threat intelligence tables:

```
/data/threat_intel/ (CSV / JSON)
        │
        ▼
threat_intel_repository.py (Startup Ingestion)
        │
        ├──────────────────────────┐
        ▼                          ▼
`threat_intel_ips`        `threat_intel_cidrs`
(Indexed by IP)           (Indexed by CIDR block)
        │                          │
        └────────────┬─────────────┘
                     ▼
       Real-Time Scoring & Alert Enrichment
```

---

## 4. Query Mechanics & Integration into Detection

During windowed flow analysis (`backend/pipeline/orchestrator.py`):

1. **IP Match Lookup:** The source IP (`src_ip`) and destination IP (`dst_ip`) are queried against `threat_intel_ips`. If a match is found:
   - The flow's base risk score is boosted by $\text{Bonus} = \text{round}(\text{ThreatScore} \times 0.25)$.
   - The threat intel category and feed source are appended to `AlertRecord` metadata.
2. **CIDR Subnet Match:** If the destination IP falls within a blacklisted CIDR in `threat_intel_cidrs`, the alert is tagged with the corresponding category (e.g. `Known Malicious C2 Subnet`).
3. **GeoIP Enrichment:** `geolocation/geolocation_service.py` queries `GeoLite2-City.mmdb` for the IP. The result is returned with `is_approximate: true` and attached to the alert. If the IP is RFC1918 (private/local), `status: "private/local"` is returned.

---

## 5. Sample Threat Intel Dataset Schema

### `data/threat_intel/malicious_ips.csv`
```csv
ip,threat_score,category,source_feed,country_code,last_seen
198.51.100.45,85,scanner,emerging_threats,DE,1772500000.0
203.0.113.12,95,botnet,alienvault,RU,1772510000.0
192.0.2.88,70,exfiltration_target,custom_black_list,US,1772520000.0
```

### `data/threat_intel/malicious_cidrs.json`
```json
[
  {
    "cidr_block": "198.51.100.0/24",
    "threat_score": 90,
    "category": "C2 Infrastructure",
    "source_feed": "emerging_threats_blocklist"
  },
  {
    "cidr_block": "203.0.113.0/24",
    "threat_score": 85,
    "category": "Known Scanner Subnet",
    "source_feed": "custom_internal"
  }
]
```
