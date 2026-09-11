-- OneWay Sentinel Migration 0001: Initial Schema Setup

CREATE TABLE IF NOT EXISTS flows (
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
    source TEXT NOT NULL CHECK(source IN ('live', 'pcap', 'simulator_normal', 'simulator_attack', 'telemetry_api'))
);

CREATE INDEX IF NOT EXISTS idx_flows_correlation ON flows(correlation_id);
CREATE INDEX IF NOT EXISTS idx_flows_src_ip ON flows(src_ip);
CREATE INDEX IF NOT EXISTS idx_flows_timestamps ON flows(start_ts, end_ts);

CREATE TABLE IF NOT EXISTS features (
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

CREATE TABLE IF NOT EXISTS model_results (
    result_id TEXT PRIMARY KEY,
    flow_id TEXT NOT NULL REFERENCES flows(flow_id) ON DELETE CASCADE,
    rf_class TEXT NOT NULL,
    rf_probability REAL NOT NULL,
    if_anomaly_score REAL NOT NULL,
    model_version TEXT NOT NULL,
    inference_ts REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_model_results_flow ON model_results(flow_id);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    flow_id TEXT NOT NULL REFERENCES flows(flow_id) ON DELETE CASCADE,
    risk_score INTEGER NOT NULL CHECK(risk_score BETWEEN 0 AND 100),
    severity TEXT NOT NULL CHECK(severity IN ('Informational', 'Low', 'Medium', 'High', 'Critical')),
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0.0 AND 1.0),
    threat_category TEXT NOT NULL,
    explanation TEXT NOT NULL,
    top_features TEXT NOT NULL,
    geolocation TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new', 'acknowledged', 'false_positive')),
    notes TEXT DEFAULT '',
    created_ts REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_correlation ON alerts(correlation_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_ts);

CREATE TABLE IF NOT EXISTS threat_intel_ips (
    ip TEXT PRIMARY KEY,
    threat_score INTEGER NOT NULL CHECK(threat_score BETWEEN 0 AND 100),
    category TEXT NOT NULL,
    source_feed TEXT NOT NULL,
    country_code TEXT DEFAULT 'XX',
    last_seen REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_threat_intel_ips_category ON threat_intel_ips(category);

CREATE TABLE IF NOT EXISTS threat_intel_cidrs (
    cidr_id TEXT PRIMARY KEY,
    cidr_block TEXT NOT NULL UNIQUE,
    threat_score INTEGER NOT NULL CHECK(threat_score BETWEEN 0 AND 100),
    category TEXT NOT NULL,
    source_feed TEXT NOT NULL,
    created_ts REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_threat_intel_cidrs_block ON threat_intel_cidrs(cidr_block);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'analyst' CHECK(role IN ('analyst', 'admin')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_ts REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
