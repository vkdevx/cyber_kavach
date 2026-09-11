# OneWay Sentinel — Component Architecture Specification (`components.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`architecture.md:107`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md#L107) and [`design.md:723`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/design.md#L723).

---

## 1. System Component Overview

OneWay Sentinel is composed of modular backend packages in Python and componentized frontend pages in React. Each component has a single defined responsibility and strict architectural boundaries.

---

## 2. Backend Component Map

```
backend/
├── api/
│   ├── main.py                - FastAPI app entrypoint, CORS, route mounting, WebSocket server
│   ├── routes_status.py       - System health, listening state, zero-outbound validation
│   ├── routes_alerts.py       - Alert feed, alert detail, triage actions (ack/FP/notes), history
│   ├── routes_simulator.py    - Control endpoints for synthetic normal/attack traffic
│   ├── routes_geolocation.py  - Approximate GeoIP lookup handler
│   ├── routes_pcap.py         - PCAP file upload and read-only replay handler
│   ├── routes_models.py       - Model loading status and degraded mode checks
│   ├── ws_manager.py          - WebSocket connection manager for client broadcasting
│   └── schemas.py             - Typed Pydantic v2 schemas for all requests/responses
│
├── risk/
│   ├── risk_engine.py         - Weighted combination of RF prob + IF score into 0-100 risk score
│   ├── severity_mapper.py     - Maps 0-100 risk score to Informational/Low/Medium/High/Critical
│   ├── confidence_engine.py   - Calculates model agreement & data sufficiency confidence (0.0-1.0)
│   └── explainer.py           - Generates 2-3 line plain-language explanation from feature importance
│
├── pipeline/
│   ├── orchestrator.py        - Linear pipeline execution: ingest → extract → score → store → push
│   └── pipeline_state.py      - Holds in-memory pipeline throughput and state metrics
│
├── core/
│   ├── logging_setup.py       - Structured JSON audit logger (ISO timestamps, correlation IDs)
│   ├── errors.py              - Application exception hierarchy and HTTP exception handlers
│   └── degraded_mode.py       - Degraded state machine (handles ML inference unavailability)
│
network/
├── passive_capture.py         - Scapy AsyncSniffer capture in read-only mode (NO send capability)
├── pcap_reader.py             - Read-only parser for uploaded PCAP captures (scapy.rdpcap)
├── packet_validator.py        - Header validation; drops malformed/incomplete packets
├── deduplicator.py            - Deduplicates duplicate/replayed packet sequences
├── flow_aggregator.py         - Groups packets into flows by 5s sliding time window
├── flow_models.py             - FlowRecord and ValidatedPacket data models
└── interface_guard.py         - Startup assertion ensuring capture NIC is read-only

ml/
├── feature_extraction.py      - Extracts 13 numerical metadata features per flow window
├── feature_normalizer.py      - Normalizes features against learned per-source baseline
├── supervised/
│   ├── random_forest_model.py - Supervised Random Forest Classifier wrapper (.predict_proba)
│   └── train_supervised.py    - Offline training script for supervised model
├── unsupervised/
│   ├── isolation_forest_model.py - Unsupervised Isolation Forest anomaly detector wrapper
│   └── train_unsupervised.py  - Offline training script for baseline anomaly detector
├── fusion/
│   └── score_fusion.py        - Executes classification policy (RF probability vs IF score)
├── model_registry.py          - Manages model artifact loading from models/trained/
└── inference_service.py       - Thread-safe inference runner

simulator/
├── normal_traffic_simulator.py - Background thread generating synthetic benign flow events
├── attack_simulator.py        - Orchestrates scenario-based attack flow generators
├── scenarios/
│   ├── port_scan.py           - High destination port diversity scenario generator
│   ├── network_scan.py        - High destination IP diversity scenario generator
│   ├── ddos_volumetric.py     - High packet-rate / low IAT flood generator
│   ├── exfiltration.py        - High byte-count volume spike generator
│   ├── beaconing.py           - Strict periodic low-volume IAT generator
│   └── unknown_anomaly.py     - Outlier statistical behavior generator
├── synthetic_event_bus.py     - Pushes synthetic flows to orchestrator ingestion queue
└── demo_controller.py         - Master state machine for live SIH demonstration scripts

geolocation/
├── geolocation_service.py     - MaxMind GeoLite2 offline .mmdb lookup wrapper
└── geo_cache.py               - In-memory cache for IP geolocation lookups

storage/
├── db.py                      - SQLite async/sync engine initialization & WAL mode config
├── models_orm.py              - SQLAlchemy ORM models (Flows, Features, ModelResults, Alerts, ThreatIntel)
└── repositories/
    ├── flow_repository.py     - Persists and queries flow records
    ├── alert_repository.py    - Persists alerts, executes triage status updates and filtered queries
    ├── model_result_repository.py - Logs raw ML inference scores
    └── threat_intel_repository.py - Queries local malicious IP/CIDR threat feeds
```

---

## 3. Frontend Component Map

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── AppShell.jsx       - Application shell mounting Header, Sidebar, and PageContainer
│   │   ├── Sidebar.jsx        - Fixed 260px navigation sidebar with pinned ZeroOutboundBadge
│   │   └── Header.jsx         - Top 64px header with title, search, notification bell, clock
│   ├── status/
│   │   ├── StatusBar.jsx      - System health & listening indicator
│   │   ├── ZeroOutboundBadge.jsx - Permanent "0 BYTES SENT BACK" trust signal badge
│   │   └── StatusPill.jsx     - Live / Degraded / Polling / Disconnected status indicator
│   ├── charts/
│   │   ├── TrafficChart.jsx   - Live volume line chart (Recharts)
│   │   └── ThreatBreakdown.jsx - Threat vs safe donut chart with centered count
│   ├── alerts/
│   │   ├── LiveAlertFeed.jsx  - Real-time updating feed of recent threat alerts
│   │   ├── SeverityBadge.jsx  - Severity pill (color + icon + label)
│   │   ├── ThreatBadge.jsx    - Named threat category badge
│   │   └── RiskGauge.jsx      - 0-100 radial risk score gauge (AlertDetail)
│   ├── simulator/
│   │   ├── SimulatorControls.jsx - Controls for baseline traffic & attack scenario injection
│   │   └── PcapUploadModal.jsx - Drag-and-drop PCAP file upload dialog
│   ├── history/
│   │   ├── FilterBar.jsx      - Date range, category, severity, source IP, and status filter bar
│   │   └── CyberTable.jsx     - Styled data grid for AlertHistory
│   └── ui/
│       ├── CyberCard.jsx      - Glass-panel card wrapper (`.cyber-card`)
│       ├── CyberPanel.jsx     - Section panel with title header
│       ├── CyberButton.jsx    - Styled button variants (primary, ghost, danger)
│       ├── CyberInput.jsx     - Monospace text input for IPs/filters
│       ├── Modal.jsx          - Reusable modal dialog
│       ├── Toast.jsx          - Action feedback toast notification
│       ├── Skeleton.jsx       - Pulsing loading placeholder
│       └── EmptyState.jsx     - Centered empty state visual layout
├── pages/
│   ├── MainDashboard.jsx      - Real-time link health dashboard
│   ├── AlertDetail.jsx        - Full evidence and triage action view per alert
│   ├── AlertHistory.jsx       - Filterable historical alert log
│   └── NetworkGraph.jsx       - P2 network relationship graph (feature-flagged)
└── hooks/
    ├── useLiveAlerts.js       - Hook for WebSocket telemetry stream & polling fallback
    ├── useAlertHistory.js     - Hook for querying filtered alert history
    ├── useStatus.js           - Hook for checking system/listening status
    └── useStats.js            - Hook for fetching live volumetric stats
```
