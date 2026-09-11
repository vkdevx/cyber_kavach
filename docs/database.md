# OneWay Sentinel — Relational Database Specification (`database.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`architecture.md:428`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md#L428) and [`rules.md:352`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L352).

---

## 1. Database Architecture Overview

OneWay Sentinel utilizes **SQLite3** in Write-Ahead Logging (WAL) mode via **SQLAlchemy 2.0+** ORM/Core. The database acts as the single durable storage boundary for flow statistics, extracted ML feature vectors, raw model inference outputs, security alerts, and threat intelligence reputation lookup tables.

### Key Structural Rules:
- **No Payload Storage:** Storing packet payload content is strictly prohibited by PRD §18 and [`rules.md:357`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L357). Only header-derived metadata is stored.
- **Traceability:** Every record from packet aggregation to alert broadcast is linked via a unique `correlation_id` UUID string.
- **Single-Writer Concurrency:** Writes are executed exclusively by the pipeline orchestrator (`backend/pipeline/orchestrator.py`) to prevent SQLite lock contention.

---

## 2. Schema DDL & Table Specifications

```sql
-- 1. FLOWS: One row per aggregated unidirectional network flow window
CREATE TABLE flows (
    flow_id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    src_ip TEXT NOT NULL,
    dst_ip TEXT NOT NULL,
    src_port INTEGER NOT NULL,
    dst_port INTEGER NOT NULL,
    protocol TEXT NOT NULL,
    packet_count INTEGER NOT NULL DEFAULT 1,
    byte_count INTEGER NOT NULL DEFAULT 0,
    start_ts REAL NOT NULL,
    end_ts REAL NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('live', 'pcap', 'simulator_normal', 'simulator_attack'))
);

CREATE INDEX idx_flows_correlation ON flows(correlation_id);
CREATE INDEX idx_flows_src_ip ON flows(src_ip);
CREATE INDEX idx_flows_timestamps ON flows(start_ts, end_ts);

-- 2. FEATURES: One row per flow containing the exact 13-feature vector fed to ML models
CREATE TABLE features (
    flow_id TEXT PRIMARY KEY REFERENCES flows(flow_id) ON DELETE CASCADE,
    total_packets REAL NOT NULL,
    total_bytes REAL NOT NULL,
    avg_packet_size REAL NOT NULL,
    flow_duration REAL NOT NULL,
    mean_iat REAL NOT NULL,
    iat_variance REAL NOT NULL,
    unique_dst_ip_count REAL NOT NULL,
    unique_dst_port_count REAL NOT NULL,
    tcp_ratio REAL NOT NULL DEFAULT 0.0,
    udp_ratio REAL NOT NULL DEFAULT 0.0,
    icmp_ratio REAL NOT NULL DEFAULT 0.0,
    small_large_pkt_ratio REAL NOT NULL,
    byte_entropy REAL NOT NULL
);

-- 3. MODEL_RESULTS: Raw supervised and unsupervised ML inference outputs per flow
CREATE TABLE model_results (
    result_id TEXT PRIMARY KEY,
    flow_id TEXT NOT NULL REFERENCES flows(flow_id) ON DELETE CASCADE,
    rf_class TEXT NOT NULL,
    rf_probability REAL NOT NULL,
    if_anomaly_score REAL NOT NULL,
    model_version TEXT NOT NULL,
    inference_ts REAL NOT NULL
);

CREATE INDEX idx_model_results_flow ON model_results(flow_id);

-- 4. ALERTS: Fused, human-facing security alerts generated when risk score > threshold
CREATE TABLE alerts (
    alert_id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    flow_id TEXT NOT NULL REFERENCES flows(flow_id) ON DELETE CASCADE,
    risk_score INTEGER NOT NULL CHECK(risk_score BETWEEN 0 AND 100),
    severity TEXT NOT NULL CHECK(severity IN ('Informational', 'Low', 'Medium', 'High', 'Critical')),
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0.0 AND 1.0),
    threat_category TEXT NOT NULL,
    explanation TEXT NOT NULL,
    top_features TEXT NOT NULL,      -- JSON array of top contributing feature names
    geolocation TEXT NOT NULL,       -- JSON object: {country, state, city, lat, lon, is_approximate: true}
    status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new', 'acknowledged', 'false_positive')),
    notes TEXT DEFAULT '',
    created_ts REAL NOT NULL
);

CREATE INDEX idx_alerts_correlation ON alerts(correlation_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created ON alerts(created_ts);

-- 5. THREAT_INTEL_IPS: Offline/local historical malicious IP reputation table
CREATE TABLE threat_intel_ips (
    ip TEXT PRIMARY KEY,
    threat_score INTEGER NOT NULL CHECK(threat_score BETWEEN 0 AND 100),
    category TEXT NOT NULL,          -- e.g. 'scanner', 'botnet', 'exfiltration_target'
    source_feed TEXT NOT NULL,       -- e.g. 'alienvault', 'emerging_threats', 'custom'
    country_code TEXT DEFAULT 'XX',
    last_seen REAL NOT NULL
);

CREATE INDEX idx_threat_intel_ips_category ON threat_intel_ips(category);

-- 6. THREAT_INTEL_CIDRS: Offline/local CIDR blacklist entries
CREATE TABLE threat_intel_cidrs (
    cidr_id TEXT PRIMARY KEY,
    cidr_block TEXT NOT NULL UNIQUE, -- e.g. '192.0.2.0/24'
    threat_score INTEGER NOT NULL CHECK(threat_score BETWEEN 0 AND 100),
    category TEXT NOT NULL,
    source_feed TEXT NOT NULL,
    created_ts REAL NOT NULL
);

CREATE INDEX idx_threat_intel_cidrs_block ON threat_intel_cidrs(cidr_block);

-- 7. USERS: User accounts for toggleable authentication and audit trail
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'analyst' CHECK(role IN ('analyst', 'admin')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_ts REAL NOT NULL
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

---

## 3. Data Access & Repository Pattern

All SQL operations are isolated inside repository classes in `storage/repositories/`. Direct raw SQL execution in FastAPI routes or pipeline code is prohibited by [`rules.md:175`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L175).

- `FlowRepository`: Creates aggregated flow records, queries recent flows by source IP.
- `FeatureRepository`: Stores extracted feature vectors linked to `flow_id`.
- `ModelResultRepository`: Logs raw Random Forest and Isolation Forest inference scores.
- `AlertRepository`: Persists alerts, handles triage updates (`status = 'acknowledged' | 'false_positive'`), queries alert history with filters.
- `ThreatIntelRepository`: Loads historical attacking IPs/CIDRs from `/data/threat_intel/` and performs fast indexed lookups during scoring.

---

## 4. SQLite Optimization & Concurrency Config

At application startup, `storage/db.py` configures the SQLite connection engine with PRAGMA settings:

```python
PRAGMA journal_mode = WAL;          -- Write-Ahead Logging for non-blocking concurrent reads
PRAGMA synchronous = NORMAL;         -- High performance with crash resiliency
PRAGMA foreign_keys = ON;            -- Enforce relational foreign key constraints
PRAGMA cache_size = -64000;          -- 64MB memory cache for indexes
```
