# OneWay Sentinel — Complete System Architecture (SIH26145)

A passive, metadata-only, one-way network threat detection system with hybrid ML (Random Forest + Isolation Forest), a live risk-scoring dashboard, and a fully simulated/controlled-lab demo mode. Designed for a 2nd-year B.Tech hackathon team, runnable on a single laptop, with zero outbound/return traffic from the monitoring path.

---

## 1. High-Level Architecture

OneWay Sentinel is a **modular monolith**, not microservices. One Python process (or a small set of cooperating local processes) owns ingestion, ML, risk scoring, storage, and API/WebSocket serving. A separate React/simple JS frontend polls/subscribes to it. Two independent front-ends feed the same pipeline:

- **Traffic Simulator** (normal + attack, synthetic — always works, no network dependency)
- **Passive Capture / PCAP replay** (optional, real Kali lab demo)

Both converge into one **Ingestion → Feature → ML → Risk → Storage → Dashboard** pipeline. The system is architected so the *only* network egress permitted anywhere in the monitoring path is: (a) reading packets passively off an interface in promiscuous/monitor mode, and (b) serving the dashboard over a local API. No component may write back onto the monitored interface.

```
┌────────────────────┐        ┌─────────────────────┐
│  Normal Simulator   │        │  Attack Simulator    │
│  (synthetic flows)  │        │  (synthetic + Kali)  │
└─────────┬───────────┘        └──────────┬───────────┘
          │                                │
          └───────────┬────────────────────┘
                       ▼
          ┌────────────────────────┐         ┌─────────────────────┐
          │  Passive Capture (opt) │────────▶│   Ingestion Layer    │
          │  (scapy, read-only)    │         │ validate/dedupe/flow │
          └────────────────────────┘         └──────────┬───────────┘
                                                          ▼
                                              ┌───────────────────────┐
                                              │  Feature Extraction    │
                                              │  + Normalization       │
                                              └──────────┬─────────────┘
                                                          ▼
                                   ┌─────────────────────────────────────┐
                                   │   Random Forest   │ Isolation Forest │
                                   └───────────┬───────────────┬─────────┘
                                               ▼               ▼
                                        ┌───────────────────────────┐
                                        │      Score Fusion          │
                                        │  (Risk Engine, 0–100)      │
                                        └──────────────┬─────────────┘
                                                        ▼
                                        ┌───────────────────────────┐
                                        │  Severity + Classification │
                                        │  + Explanation Generator   │
                                        └──────────────┬─────────────┘
                                                        ▼
                                        ┌───────────────────────────┐
                                        │  Storage (SQLite)          │
                                        └──────────────┬─────────────┘
                                                        ▼
                                        ┌───────────────────────────┐
                                        │  API + WebSocket layer     │
                                        └──────────────┬─────────────┘
                                                        ▼
                                        ┌───────────────────────────┐
                                        │  Dashboard (React SPA)     │
                                        └────────────────────────────┘
```

---

## 2. ASCII Architecture Diagram (Component Ownership View)

```
                              LAPTOP (single host)
 ┌────────────────────────────────────────────────────────────────────────┐
 │                                                                        │
 │  ┌───────────────┐   ┌──────────────────┐    ┌────────────────────┐   │
 │  │  simulator/    │   │   network/        │    │   ml/               │   │
 │  │  - normal_traffic│  │  - passive_capture│    │  - random_forest    │   │
 │  │  - attack_sim  │──▶│  - pcap_reader    │───▶│  - isolation_forest │   │
 │  │  - demo_ctrl   │   │  - flow_aggregator│    │  - feature_pipeline │   │
 │  └───────────────┘   │  - validator      │    │  - model_registry   │   │
 │                       └──────────────────┘    └──────────┬──────────┘   │
 │                                                            ▼             │
 │                                                  ┌────────────────────┐ │
 │                                                  │   backend/risk/     │ │
 │                                                  │  - risk_engine      │ │
 │                                                  │  - severity_mapper  │ │
 │                                                  │  - confidence_engine│ │
 │                                                  │  - explainer        │ │
 │                                                  └──────────┬──────────┘ │
 │                                                              ▼           │
 │  ┌───────────────┐     ┌──────────────────┐     ┌────────────────────┐ │
 │  │  storage/      │◀───│  backend/api/     │────▶│  frontend/ (React)  │ │
 │  │  SQLite DB     │     │  REST + WS server │     │  Dashboard          │ │
 │  └───────────────┘     └──────────────────┘     └────────────────────┘ │
 │                                                                        │
 │  ┌────────────────────────────────────────────────────────────────┐  │
 │  │  geolocation/  (local MaxMind GeoLite2 DB — read-only lookups)  │  │
 │  └────────────────────────────────────────────────────────────────┘  │
 └────────────────────────────────────────────────────────────────────────┘
        ▲
        │  ONE-WAY ONLY: interface read (monitor/mirror port)
        │  NEVER: writes, resets, probes, ACKs back onto this interface
 ┌──────┴──────────────┐
 │ Monitored Interface  │◀──── (Kali attacker VM, isolated lab network)
 │ (span/mirror/tap)    │
 └───────────────────────┘
```

---

## 3. Complete Folder Tree

```
oneway-sentinel/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes_status.py
│   │   ├── routes_alerts.py
│   │   ├── routes_simulator.py
│   │   ├── routes_geolocation.py
│   │   ├── routes_pcap.py
│   │   ├── routes_models.py
│   │   ├── ws_manager.py
│   │   └── schemas.py
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── risk_engine.py
│   │   ├── severity_mapper.py
│   │   ├── confidence_engine.py
│   │   └── explainer.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   └── pipeline_state.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging_setup.py
│   │   ├── errors.py
│   │   └── degraded_mode.py
│   └── app.py
│
├── network/
│   ├── __init__.py
│   ├── passive_capture.py
│   ├── pcap_reader.py
│   ├── packet_validator.py
│   ├── deduplicator.py
│   ├── flow_aggregator.py
│   ├── flow_models.py
│   └── interface_guard.py
│
├── ml/
│   ├── __init__.py
│   ├── feature_extraction.py
│   ├── feature_normalizer.py
│   ├── supervised/
│   │   ├── __init__.py
│   │   ├── random_forest_model.py
│   │   └── train_supervised.py
│   ├── unsupervised/
│   │   ├── __init__.py
│   │   ├── isolation_forest_model.py
│   │   └── train_unsupervised.py
│   ├── fusion/
│   │   ├── __init__.py
│   │   └── score_fusion.py
│   ├── model_registry.py
│   └── inference_service.py
│
├── datasets/
│   ├── raw/
│   ├── cleaned/
│   ├── processed/
│   ├── feature_engineered/
│   └── pipeline/
│       ├── __init__.py
│       ├── loader.py
│       ├── cicids2017_adapter.py
│       ├── cse_cic_ids2018_adapter.py
│       ├── nsl_kdd_adapter.py
│       ├── unsw_nb15_adapter.py
│       ├── forward_flow_filter.py
│       └── feature_builder.py
│
├── models/
│   ├── trained/
│   │   ├── random_forest_v1.pkl
│   │   └── isolation_forest_v1.pkl
│   ├── evaluation/
│   │   ├── rf_metrics.json
│   │   └── if_metrics.json
│   └── metadata/
│       └── model_registry.json
│
├── simulator/
│   ├── __init__.py
│   ├── normal_traffic_simulator.py
│   ├── attack_simulator.py
│   ├── scenarios/
│   │   ├── __init__.py
│   │   ├── port_scan.py
│   │   ├── network_scan.py
│   │   ├── ddos_volumetric.py
│   │   ├── exfiltration.py
│   │   ├── beaconing.py
│   │   └── unknown_anomaly.py
│   ├── synthetic_event_bus.py
│   └── demo_controller.py
│
├── geolocation/
│   ├── __init__.py
│   ├── geolocation_service.py
│   ├── geo_cache.py
│   └── data/
│       └── GeoLite2-City.mmdb   (not committed — download instructions in docs/)
│
├── storage/
│   ├── __init__.py
│   ├── db.py
│   ├── models_orm.py
│   ├── migrations/
│   │   └── 0001_init.sql
│   └── repositories/
│       ├── __init__.py
│       ├── flow_repository.py
│       ├── alert_repository.py
│       └── model_result_repository.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── default.yaml
│   ├── risk_weights.yaml
│   └── .env.example
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   ├── client.js
│   │   │   └── ws.js
│   │   ├── pages/
│   │   │   ├── MainDashboard.jsx
│   │   │   ├── AlertDetail.jsx
│   │   │   ├── AlertHistory.jsx
│   │   │   └── NetworkGraph.jsx
│   │   ├── components/
│   │   │   ├── StatusBar.jsx
│   │   │   ├── ZeroOutboundBadge.jsx
│   │   │   ├── TrafficChart.jsx
│   │   │   ├── ThreatBreakdown.jsx
│   │   │   ├── LiveAlertFeed.jsx
│   │   │   ├── SimulatorControls.jsx
│   │   │   └── FilterBar.jsx
│   │   └── styles/
│   └── public/
│
├── scripts/
│   ├── setup_env.sh
│   ├── download_datasets.sh
│   ├── train_models.sh
│   ├── run_dev.sh
│   ├── run_demo.sh
│   └── verify_zero_outbound.py
│
├── tests/
│   ├── unit/
│   │   ├── test_feature_extraction.py
│   │   ├── test_risk_engine.py
│   │   ├── test_severity_mapper.py
│   │   ├── test_confidence_engine.py
│   │   └── test_explainer.py
│   ├── integration/
│   │   ├── test_pipeline_end_to_end.py
│   │   ├── test_api_routes.py
│   │   └── test_dashboard_data_contract.py
│   ├── ml/
│   │   ├── test_random_forest_inference.py
│   │   └── test_isolation_forest_inference.py
│   ├── network/
│   │   ├── test_passive_ingestion.py
│   │   └── test_zero_outbound.py
│   └── simulator/
│       └── test_scenarios.py
│
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   ├── demo.md
│   ├── kali_lab_setup.md
│   ├── dataset_notes.md
│   └── api_reference.md
│
├── .env.example
├── requirements.txt
├── pyproject.toml
├── README.md
└── docker-compose.yml   (optional, P2)
```

---

## 4. Explanation of Every Folder

| Folder | What it does | Why it exists | Who imports it | Must NOT contain | Priority |
|---|---|---|---|---|---|
| `backend/api/` | HTTP + WebSocket surface | Single boundary between frontend and system | `frontend/`, tests | ML/risk logic | P0 |
| `backend/risk/` | Risk scoring, severity, confidence, explanations | Isolates scoring math from ML models | `backend/pipeline`, tests | Model training code, DB code | P0 |
| `backend/pipeline/` | Orchestrates the full flow → feature → ML → risk → storage sequence | Single place that wires stages together | `backend/app.py` | Business rules for scoring (belongs in `risk/`) | P0 |
| `backend/core/` | Logging, error types, degraded-mode state machine | Cross-cutting concerns | everything in `backend/` | Feature/ML/risk logic | P0 |
| `network/` | Passive capture, validation, dedup, flow aggregation | Only place allowed to touch NICs/PCAPs | `backend/pipeline` | Any `send()`/`sendto()` call, ML code | P0 |
| `ml/` | Feature extraction, RF, Isolation Forest, fusion, inference | Isolates ML from ingestion/risk | `backend/pipeline` | Network capture code, DB writes | P0 |
| `datasets/` | Raw → cleaned → processed → feature-engineered dataset stages, one folder each | Reproducible, non-hardcoded dataset pipeline | `ml/*/train_*.py` | Trained model binaries (those live in `models/`) | P1 (training-time only, not runtime) |
| `models/` | Trained model artifacts + evaluation metrics + registry metadata | Decouples training from inference | `ml/model_registry.py` | Training code | P0 |
| `simulator/` | Normal traffic generator, attack scenarios, demo controller | Makes the demo work with zero external dependency | `backend/pipeline` (as an alternate/parallel ingestion source) | Real capture code | P0 |
| `geolocation/` | IP → approximate location, with caching | Isolated, optional, clearly-labeled "approximate" service | `backend/risk/explainer`, `backend/api/routes_geolocation` | Any claim of exact/attacker location | P1 |
| `storage/` | SQLite schema, ORM models, repositories | Single persistence boundary | `backend/pipeline`, `backend/api` | Payload bytes, business logic | P0 |
| `config/` | Centralized settings, YAML configs, env template | No hardcoded magic numbers/paths anywhere else | everything | Secrets committed in plaintext | P0 |
| `frontend/` | React dashboard SPA | User-facing visualization | — | Business logic, ML logic | P0 (Main Dashboard), P1 (Alert Detail/History), P2 (Network Graph) |
| `scripts/` | Setup, training, dev-run, demo-run, zero-outbound verification | Reproducibility for judges/teammates | developer CLI | Application runtime logic | P0/P1 mixed (see §19 script) |
| `tests/` | All automated tests, mirrors source structure | Confidence + judge credibility | CI, developer CLI | — | P0 (subset), P1 (full coverage) |
| `docs/` | PRD, architecture doc, demo script, Kali lab guide, dataset notes, API reference | Onboarding + SIH judge documentation | — | Executable code | P0 (demo.md), P1 (rest) |

---

## 5. Explanation of Every Important File

**`network/passive_capture.py`** — Opens the monitored interface in read-only/promiscuous mode (via `scapy.sniff` or `AsyncSniffer`) and yields raw packet metadata. Never opens a raw socket for sending. Imported only by `backend/pipeline/orchestrator.py`. Must NOT contain any `send`, `sendp`, `sr`, `sr1` calls — this is enforced by `scripts/verify_zero_outbound.py` (static grep) and `tests/network/test_zero_outbound.py` (runtime). **P0**.

**`network/interface_guard.py`** — A thin wrapper that asserts, at process start, that the configured capture interface is opened in a read-only capture mode and refuses to start if any send-capable socket is requested on that interface. Acts as the architectural "diode" enforcement point. **P0**.

**`network/flow_aggregator.py`** — Groups deduplicated packets into unidirectional flow records keyed by (src_ip, dst_ip, src_port, dst_port, protocol) within a configurable time window (`config/default.yaml: flow_window`). Emits a `FlowRecord` object. **P0**.

**`ml/feature_extraction.py`** — Converts a `FlowRecord`/window of flows into the fixed feature vector described in PRD §5 (packet count, byte count, mean IAT, IAT variance, unique dest IP/port counts, protocol distribution, packet-size ratios, entropy). Pure function, no I/O. **P0**.

**`ml/supervised/random_forest_model.py`** — Loads `models/trained/random_forest_v1.pkl`, exposes `predict_proba(feature_vector) -> {class, probability}`. **P0**.

**`ml/unsupervised/isolation_forest_model.py`** — Loads `models/trained/isolation_forest_v1.pkl`, exposes `anomaly_score(feature_vector) -> float`, trained primarily on benign flows. **P0**.

**`ml/fusion/score_fusion.py`** — Combines supervised probability + anomaly score into a single normalized signal per PRD; delegates final 0–100 scaling to `backend/risk/risk_engine.py` (keeps ML package free of business-scoring policy). **P0**.

**`backend/risk/risk_engine.py`** — Takes fused ML signal → 0–100 risk score using configurable weights from `config/risk_weights.yaml`. No magic numbers in code. **P0**.

**`backend/risk/severity_mapper.py`** — Pure lookup: score → {Informational, Low, Medium, High, Critical} per the PRD bands. **P0**.

**`backend/risk/confidence_engine.py`** — Derives a confidence value from model agreement (RF probability vs IF anomaly score concordance) and data sufficiency (flow duration/packet count). **P0**.

**`backend/risk/explainer.py`** — Builds the human-readable explanation string from the actual top-contributing features (e.g., feature importances from RF + z-score deviation from per-source baseline for IF-flagged flows). Never fabricates text unconnected to real feature values. Exposes a hook point for future SHAP value injection. **P0 (rule-based MVP), P2 (SHAP)**.

**`backend/pipeline/orchestrator.py`** — The single function/class that wires: ingestion source (real or simulated) → validator → dedup → aggregator → feature extractor → normalizer → RF + IF → fusion → risk engine → severity → confidence → explainer → storage → WS broadcast. This is the literal implementation of the §9 pipeline. **P0**.

**`backend/core/degraded_mode.py`** — If ML inference throws, catches it, marks pipeline state `DEGRADED`, continues passing flows to storage/dashboard with `risk_score=null, severity="Unknown - ML Unavailable"` rather than crashing ingestion. **P0**.

**`simulator/normal_traffic_simulator.py`** — Emits synthetic benign `FlowRecord`-shaped events (TCP/UDP, varied size/timing/destination) directly into the same queue the orchestrator reads from — independent process/thread, start/stop controllable via API. **P0**.

**`simulator/attack_simulator.py`** + `simulator/scenarios/*.py` — Each scenario is a small class with `start()/stop()` emitting synthetic flow events matching that attack's statistical signature (e.g., `port_scan.py` emits many unique dest-port, low-byte flows from one source). Independent of Kali; also documents what real Kali command reproduces the same shape (cross-referenced in `docs/demo.md`). **P0 (synthetic), P1 (Kali doc)**.

**`simulator/demo_controller.py`** — Orchestrates the full SIH demo script (§21) as a state machine callable from one dashboard button or CLI script. **P1**.

**`geolocation/geolocation_service.py`** — `lookup(ip) -> {country, state, city, lat, lon, is_approximate: true} | "unavailable" | "private/local"`. Uses a local MaxMind GeoLite2 file (no live external calls required for the demo) or a configured provider if available. Wraps every result with an explicit "Approximate Location" label. **P1**.

**`geolocation/geo_cache.py`** — In-memory/SQLite cache keyed by IP to avoid repeat lookups. **P1**.

**`storage/db.py`** — SQLite connection/session management (or SQLAlchemy engine). **P0**.

**`storage/repositories/*.py`** — Repository pattern: `flow_repository`, `alert_repository`, `model_result_repository` — the only files allowed to write SQL. Keeps persistence out of pipeline/business logic. **P0**.

**`backend/api/main.py`** — FastAPI (recommended) app entrypoint, mounts all routers + WebSocket manager. **P0**.

**`backend/api/ws_manager.py`** — Manages WebSocket client connections and broadcasts new alerts/stat updates pushed by the orchestrator. **P0**.

**`config/settings.py`** — Loads `default.yaml` + `.env` + `risk_weights.yaml` into one typed settings object; every other module reads config only through this, never hardcodes a path/threshold. **P0**.

**`scripts/verify_zero_outbound.py`** — Static + runtime check (grep for socket-send primitives in `network/`, plus a live test that opens the capture interface and asserts no packets are ever written to it) used both in CI and as a literal demo step for judges. **P0**.

**`docs/demo.md`** — Step-by-step Kali lab instructions restricted to an authorized, isolated local target (see §13). **P0 for the demo, doc-only artifact**.

---

## 6. Data Flow Between Modules

```
RawPacket (network/) 
   → ValidatedPacket 
   → DedupedPacket 
   → FlowRecord {src_ip,dst_ip,src_port,dst_port,proto,pkt_count,byte_count,
                  timestamps[],ttl_flags(meta only)}
   → FeatureVector {13 numeric features, source_baseline_ref}
   → NormalizedFeatureVector
   → { rf_output: {class, probability}, if_output: {anomaly_score} }
   → FusedSignal {combined_score_0_1, agreement}
   → RiskResult {risk_score_0_100, severity, confidence, threat_category}
   → Explanation {text, top_features[]}
   → AlertRecord {all of the above + flow_id + correlation_id + geolocation}
   → SQLite row(s) (flows, features, alerts tables, linked by correlation_id)
   → WebSocket AlertEvent (JSON) → frontend store → UI components
```

Every object above is a typed dataclass/Pydantic model defined once (`network/flow_models.py`, `backend/api/schemas.py`) and reused across the pipeline — no ad hoc dicts crossing module boundaries.

---

## 7. ML Architecture

- **Supervised:** `RandomForestClassifier` (scikit-learn), trained on CICIDS2017/CSE-CIC-IDS2018 (forward-flow-filtered), multi-class over {Benign, Port Scan, Network Scan, DDoS/Flood, Exfiltration, Beaconing (if evidence supports)}. Outputs class + probability.
- **Unsupervised:** `IsolationForest` (scikit-learn), trained primarily on benign flows from the same pipeline, outputs an anomaly score; flows anomalous but not confidently classified by RF are labeled `Unknown Anomaly`.
- **Fusion policy:** if RF probability for a known class exceeds a configurable confidence threshold → classify as that known threat; else if IF anomaly score exceeds its threshold → `Unknown Anomaly`; else → benign. Both scores still feed the 0–100 risk score jointly (weighted sum, weights in `config/risk_weights.yaml`).
- **No deep learning** — unjustified for tabular flow metadata at this scale; RF + IF is the PRD-mandated, interpretable, laptop-trainable pair.
- **Explainability:** RF feature_importances_ per prediction (or per-instance via simple permutation/feature-deviation for MVP) feeds `explainer.py`; SHAP is a P2 drop-in behind the same interface.

---

## 8. Network Architecture

**Mode A — Live passive capture:** `scapy.AsyncSniffer` (or `pypcap`/`pcapy-ng`) on a mirrored/SPAN/tap interface, `promisc=True`, capturing headers only (no payload retained past feature extraction — payload bytes are read into memory by libpcap but never stored or forwarded, and the extraction step discards them immediately). Must run on an interface with **no IP configured for sending** where possible (true passive tap), or at minimum never call any send primitive against it — enforced by `interface_guard.py`.

**Mode B — Simulator/PCAP:** Synthetic JSON flow events (from `simulator/`) or PCAP file replay (`network/pcap_reader.py`, using `scapy.rdpcap` — read-only file parsing, never re-injected onto a live interface) are converted into the same `FlowRecord` shape and pushed into the identical queue the orchestrator consumes from Mode A. This is why both modes "eventually enter the same feature-extraction and ML pipeline" — they share one ingestion queue interface.

---

## 9. Pipeline (as implemented)

Matches PRD §9 exactly; implemented as one linear call chain inside `backend/pipeline/orchestrator.py`, each stage a pure function/class with a single typed input/output object (see §6). This makes every stage independently unit-testable (see §18 tests) and swappable (e.g., replace RF with another sklearn model without touching ingestion).

---

## 10. Database Schema (SQLite, MVP)

```sql
-- flows: one row per aggregated flow
CREATE TABLE flows (
  flow_id TEXT PRIMARY KEY,
  correlation_id TEXT NOT NULL,
  src_ip TEXT, dst_ip TEXT,
  src_port INTEGER, dst_port INTEGER,
  protocol TEXT,
  packet_count INTEGER, byte_count INTEGER,
  start_ts REAL, end_ts REAL,
  source TEXT CHECK(source IN ('live','pcap','simulator_normal','simulator_attack'))
);

-- features: one row per flow, the exact vector fed to ML
CREATE TABLE features (
  flow_id TEXT PRIMARY KEY REFERENCES flows(flow_id),
  total_packets REAL, total_bytes REAL, avg_packet_size REAL,
  flow_duration REAL, mean_iat REAL, iat_variance REAL,
  unique_dst_ip_count REAL, unique_dst_port_count REAL,
  protocol_distribution TEXT,   -- JSON
  small_large_pkt_ratio REAL, byte_entropy REAL
);

-- model_results: raw ML output per flow
CREATE TABLE model_results (
  flow_id TEXT REFERENCES flows(flow_id),
  rf_class TEXT, rf_probability REAL,
  if_anomaly_score REAL,
  model_version TEXT,
  inference_ts REAL
);

-- alerts: fused, human-facing record
CREATE TABLE alerts (
  alert_id TEXT PRIMARY KEY,
  correlation_id TEXT NOT NULL,
  flow_id TEXT REFERENCES flows(flow_id),
  risk_score INTEGER, severity TEXT, confidence REAL,
  threat_category TEXT,
  explanation TEXT, top_features TEXT, -- JSON
  geolocation TEXT, -- JSON, always includes is_approximate flag
  status TEXT CHECK(status IN ('new','acknowledged','false_positive')) DEFAULT 'new',
  notes TEXT,
  created_ts REAL
);
```

No table ever stores packet payload bytes. `correlation_id` threads packet→flow→feature→alert traceability end to end (§14 requirement).

---

## 11. API Architecture

REST (FastAPI) grouped by router, business logic strictly outside route handlers (handlers call into `backend/pipeline`, `backend/risk`, `storage/repositories`, `simulator`, `geolocation` — never implement logic inline):

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/status` | system/passive-mode/degraded status |
| GET | `/api/stats/live` | packets scanned, flows analyzed, threats detected, safe traffic |
| GET | `/api/alerts` | live + historical, filterable |
| GET | `/api/alerts/{id}` | full alert detail |
| POST | `/api/alerts/{id}/ack` | acknowledge |
| POST | `/api/alerts/{id}/false-positive` | mark false positive |
| POST | `/api/alerts/{id}/notes` | add notes |
| GET | `/api/alerts/history` | filtered history (date, category, severity, src IP, status) |
| POST | `/api/simulator/normal/start` \| `/stop` | control normal traffic sim |
| POST | `/api/simulator/attack/{scenario}/start` \| `/stop` | control a specific attack scenario |
| POST | `/api/pcap/upload` | upload + replay a PCAP |
| GET | `/api/models/status` | model versions, load state, degraded flag |
| GET | `/api/geolocation/{ip}` | approximate geolocation lookup |
| WS | `/ws/alerts` | real-time alert + stat push |

---

## 12. Dashboard Architecture

- **MainDashboard.jsx**: status bar (incl. `ZeroOutboundBadge`), packets/flows/threats/safe counters, `TrafficChart`, `ThreatBreakdown`, `LiveAlertFeed` (subscribes to `/ws/alerts`).
- **AlertDetail.jsx**: full record per §12 fields, including "Approximate Location" (never "Attacker Location"), top contributing features, recent source history (queried by src_ip).
- **AlertHistory.jsx**: `FilterBar` (date, category, severity, src IP, status) + table + row actions (Acknowledge / False Positive / Notes) calling the corresponding POST endpoints.
- **NetworkGraph.jsx (P2)**: Source→Destination graph, edge thickness = traffic volume, node/edge color = risk.

State management: simple React context + WS event reducer is sufficient — no need for Redux at this scale.

---

## 13. Simulator Architecture

Two independent, start/stoppable emitters (`normal_traffic_simulator.py`, `attack_simulator.py` + `scenarios/*.py`), each running in its own thread/asyncio task, pushing directly into the ingestion queue — structurally identical to how a real capture packet would enter, so the ML/risk/storage/dashboard code cannot tell (and doesn't need to know) whether traffic is real or synthetic. Controlled entirely via the `/api/simulator/*` routes and mirrored in `SimulatorControls.jsx`.

---

## 14. Kali Controlled-Lab Demonstration Architecture

- Kali VM and a single authorized lab target VM live on an **isolated virtual/host-only network segment**, never routed to the internet or any production network.
- Traffic is mirrored (VM hypervisor promiscuous/mirror mode, or a physical SPAN port if using real hardware) to the interface OneWay Sentinel listens on.
- `docs/demo.md` documents exact, minimal, authorized-target-only commands (e.g., `nmap` scan types, `hping3` flood, a small script for beacon-style periodic requests) run *only* against the lab target's private IP — explicitly never against any external/public host.
- OneWay Sentinel's capture interface is the mirror port only; it has no route back into the Kali/lab segment for sending.

---

## 15. Normal Traffic Generation Approach

Two layers, matching PRD:
1. **Synthetic (primary, always-on fallback):** `normal_traffic_simulator.py` generates flow-shaped events directly — variable packet sizes, inter-arrival times, multiple destinations, periodic legitimate patterns (e.g., simulated DNS/NTP-like polling), occasional legitimate bursts (e.g., simulated file sync). No real packets required.
2. **Real lab traffic (optional, for authenticity):** in the isolated lab, ordinary benign activity — ICMP pings, `curl`/`wget` to the lab target, simple HTTP/SSH sessions, periodic cron-like scripts — generated *within the same isolated segment*, captured by the same mirror port.

The simulator is documented as the **reliable fallback**: if live capture fails during the SIH demo, judges still see a fully working, realistic dashboard.

---

## 16. Attack Simulation Approach

Each of the 6 scenarios is implemented twice, sharing one signature definition:
- **Synthetic emitter** (`simulator/scenarios/*.py`) — statistically shaped flow events (e.g., `port_scan.py`: single source, many destination ports, tiny per-flow byte counts, tight inter-arrival times).
- **Kali equivalent** (documented in `docs/demo.md`) — the real command producing the same statistical shape against the authorized lab target only.

Both land in the identical pipeline, so detection logic is exercised identically regardless of source.

---

## 17. Geolocation Architecture

`geolocation_service.lookup(ip)`:
1. If IP is private/RFC1918/loopback → return `{status: "private/local"}`.
2. Else check `geo_cache` (SQLite/in-memory, TTL-free since IP→geo rarely changes) — return cached hit if present.
3. Else query local MaxMind GeoLite2 `.mmdb` (offline, no internet dependency for the demo) or a configured external provider if explicitly enabled in `config/default.yaml`.
4. Return `{country, state, city, lat, lon, is_approximate: true}` or `{status: "unavailable"}`.
5. Every consumer (API, `explainer.py`, frontend) renders this as **"Approximate Location"**, never as attacker attribution, and the UI/API contract makes `is_approximate` a mandatory field so no rendering path can silently drop the caveat.

---

## 18. Security / Zero-Return Architecture

- **Outbound-prohibited zone:** the entirety of `network/` (capture + PCAP read) — no `send`, `sendp`, `sr`, `sr1`, raw-socket-write, or ICMP/TCP-reset primitive is permitted anywhere in this package. Enforced by static grep in `scripts/verify_zero_outbound.py` and a runtime test in `tests/network/test_zero_outbound.py` that asserts zero bytes are ever written to the capture interface's socket handle across a full test run.
- **Only component allowed to talk to the dashboard:** `backend/api/` (REST + WebSocket) — this is a local-loopback/LAN service unrelated to the monitored interface; it runs on a separate network context (typically the host's normal management NIC, not the mirror port).
- **Only component allowed to reach geolocation services (if a remote provider is configured):** `geolocation/geolocation_service.py`, and only over the management network, never over the monitored interface, and only for IP metadata lookups (never packet forwarding).
- **Monitoring interface isolation:** the capture interface is configured as a mirror/SPAN/tap port (or a host-only virtual interface in the lab), architected to receive only; `interface_guard.py` refuses process startup if a send-capable socket is ever requested against the configured capture interface name.
- **Software-simulated diode representation:** the boundary between `network/` (read-only) and everything downstream is a one-directional queue (`asyncio.Queue`/`multiprocessing.Queue`) — data can only be `put()` by capture/simulator producers and `get()` by the pipeline consumer; there is no API in the codebase for the consumer side to write back into that queue's producer side or onto the interface.

---

## 19. Testing Architecture

- **Unit:** feature extraction math, risk engine weighting, severity band mapping, confidence calculation, explanation generation (given fixed feature inputs, assert stable explanation text pattern).
- **ML inference tests:** RF and IF loaded from fixture models, deterministic outputs on fixed feature vectors.
- **Risk-score tests:** boundary tests at each severity band edge (19/20, 39/40, 59/60, 79/80).
- **Simulator tests:** each scenario emits the expected statistical shape (e.g., port scan → unique_dst_port_count above threshold).
- **API tests:** every route in §11, including error paths (invalid alert id, malformed PCAP upload).
- **Dashboard integration tests:** WS event → store update → component render (React Testing Library), and a data-contract test that the WS payload matches `backend/api/schemas.py`.
- **Passive-ingestion tests:** validator rejects malformed packets, deduplicator drops repeats, aggregator windows correctly.
- **Zero-outbound verification test:** the flagship test — starts capture (or a loopback-simulated interface), floods it with adversarial "response-provoking" scenarios, asserts the interface's send counters remain exactly zero for the entire run. This test is run live in front of judges per PRD.

---

## 20. P0/P1/P2 Implementation Plan

**P0 (MVP, demo-critical):** `network/` passive ingestion + validator/dedup/aggregator, `simulator/normal_traffic_simulator.py` + core attack scenarios (synthetic), `ml/feature_extraction.py`, `ml/supervised`, `ml/unsupervised`, `backend/risk/*`, `storage/` (flows, features, alerts), `backend/api` core routes + WS, `frontend` MainDashboard + LiveAlertFeed + AlertHistory (basic), `ZeroOutboundBadge` + `scripts/verify_zero_outbound.py`.

**P1 (should-have):** PCAP upload/replay, full threat classification labeling, `simulator/demo_controller.py` + demo control panel UI, `geolocation/`, richer AlertDetail (source history, top features).

**P2 (if time permits):** SHAP integration behind `explainer.py`'s existing interface, `NetworkGraph.jsx`, authentication on the API, simulated periodic retraining, advanced analytics/trend views.

P2 work is deliberately decoupled (SHAP behind an interface, graph as an additional page, auth as middleware that can be toggled off) so it never blocks or destabilizes P0.

---

## 21. Recommended Technology Stack

- **Backend:** Python 3.11, FastAPI (REST + native WebSocket support, async-friendly for the sniff loop), Uvicorn.
- **Capture:** `scapy` (simplest for a student team; `AsyncSniffer` for non-blocking capture) — swappable later for `pypcap`/`dpkt` if performance requires.
- **ML:** scikit-learn (`RandomForestClassifier`, `IsolationForest`), `joblib` for model persistence, `pandas`/`numpy` for feature engineering.
- **Storage:** SQLite via SQLAlchemy (simple, zero-ops, laptop-friendly; trivially swappable for Postgres later if ever needed).
- **Realtime:** native WebSocket via FastAPI (see §22 for rationale over SSE/polling).
- **Frontend:** React (Vite), lightweight charting (`recharts` or `chart.js`), plain CSS or Tailwind.
- **Geolocation:** MaxMind GeoLite2 (offline `.mmdb`, via `geoip2` Python package).
- **Testing:** `pytest`, `pytest-asyncio`, `httpx` (API tests), React Testing Library.
- **Packaging/config:** `pydantic-settings` for typed config, `python-dotenv` for `.env`.

---

## 22. Exact Development Sequence

1. Scaffold repo structure (§3) + `config/settings.py` + logging.
2. Build `storage/` schema + repositories (empty DB, testable in isolation).
3. Build `simulator/normal_traffic_simulator.py` first — gives the team a live data source on day one without needing capture or Kali.
4. Build `network/flow_models.py`, `flow_aggregator.py`, `packet_validator.py`, `deduplicator.py` against simulator output.
5. Build `ml/feature_extraction.py` + `feature_normalizer.py`, unit-tested against synthetic flows.
6. Build `datasets/pipeline/*` adapters, train initial RF + IF (`scripts/train_models.sh`), save to `models/trained/`.
7. Build `ml/inference_service.py` + `ml/fusion/score_fusion.py`.
8. Build `backend/risk/*` (risk engine, severity mapper, confidence engine, explainer).
9. Wire `backend/pipeline/orchestrator.py` end-to-end against the simulator.
10. Build `backend/api/*` + `ws_manager.py`.
11. Build `frontend/` MainDashboard against the live API/WS.
12. Add `simulator/attack_simulator.py` + scenarios; verify each produces a distinguishable alert.
13. Add AlertDetail + AlertHistory pages + acknowledge/false-positive/notes routes.
14. Add `network/passive_capture.py` + `interface_guard.py` for real Kali-lab capture; validate against `pcap_reader.py` replay first (safer to debug).
15. Add `geolocation/`.
16. Add `scripts/verify_zero_outbound.py` + zero-outbound tests; run continuously from here on.
17. Add `simulator/demo_controller.py` + polish demo script.
18. Stretch: SHAP, NetworkGraph, auth.

---

## 23. SIH Live-Demo Sequence

Implements PRD §21 exactly, driven by `simulator/demo_controller.py` and/or a single `scripts/run_demo.sh`:

1. Start OneWay Sentinel → dashboard shows healthy/passive status + `ZeroOutboundBadge`.
2. Start normal traffic simulator → dashboard shows safe traffic climbing.
3. Start port/network scan scenario (Kali or synthetic) → alert appears within ~2s with risk score, category, evidence.
4. Start flood/DDoS-like scenario → high-volume anomaly detected.
5. Start beaconing/covert scenario → Isolation Forest flags it; shown as "Unknown Anomaly" if RF confidence is insufficient.
6. Show Alert History with filters.
7. Show Network Relationship View (if implemented).
8. Run `verify_zero_outbound.py` live / show the badge + test output to prove zero outbound capability.

---

## 24. Potential Failure Points and Fallback Mechanisms

| Failure | Fallback |
|---|---|
| Live capture fails / no mirror port available at venue | Fall back entirely to `normal_traffic_simulator.py` + `attack_simulator.py` synthetic scenarios — demo is scripted to work with zero live network dependency |
| ML model fails to load or throws at inference | `degraded_mode.py` catches it; ingestion + dashboard continue with `severity="Unknown - ML Unavailable"` rather than crashing |
| Geolocation DB/provider unavailable | Show "Location unavailable"; never block alert generation on geolocation |
| WebSocket disconnects | Frontend falls back to short-interval polling of `/api/alerts` until WS reconnects |
| SQLite write contention/corruption risk under load | Single-writer pattern via one pipeline process; WAL mode enabled |
| Kali VM/network issues at venue | Entire demo scripted to run identically via synthetic scenarios, rehearsed as primary path, Kali as bonus/optional live flourish |
| Dataset download unavailable at venue | Models pre-trained ahead of time and committed to `models/trained/`; `datasets/raw` is dev-time only, not a demo dependency |
| Time pressure | P2 features (SHAP, graph, auth) are structurally decoupled and can be skipped without touching P0 code paths |

---

## Final Recommendation

Build exactly the structure above, in the exact development sequence in §22. Start with the synthetic simulator as the primary data source (it de-risks the entire demo), treat live Kali capture as an enhancement layered on afterward through the same ingestion interface, and keep the zero-outbound guarantee enforced at three layers simultaneously: structurally (one-directional queue, no send primitives in `network/`), procedurally (code review checklist), and empirically (a runtime test you can run live for the judges).
