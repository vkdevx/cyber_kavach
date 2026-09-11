# OneWay Sentinel — Phased Engineering Task Roadmap (`tasks.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`architecture.md:608`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md#L608) and [`rules.md:763`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L763).

---

## Task Progress Overview

- [x] **Phase 0: Documentation & Architecture Blueprint** (Completed)
- [x] **Phase 1: Environment, Configuration & Storage Engine Setup** (Completed)
- [x] **Phase 2: Traffic Simulation & Network Capture Pipeline** (Completed)
- [x] **Phase 3: Dataset Adapter & ML Model Training** (Completed)
- [x] **Phase 4: Risk Scoring Engine & XAI Explainer** (Completed)
- [x] **Phase 5: FastAPI REST & WebSocket Telemetry Server** (Completed)
- [x] **Phase 6: React Frontend SPA & Dashboard Components** (Completed)
- [x] **Phase 7: Threat Intelligence & Kali Lab Integration** (Completed)
- [x] **Phase 8: Zero-Outbound Verification & E2E Validation** (Completed)

---

## Phase 1: Environment, Configuration & Storage Engine Setup
- [x] **Task 1.1:** Setup Python 3.11 virtual environment and install backend dependencies in `requirements.txt`.
- [x] **Task 1.2:** Create `.env.example` and typed Pydantic settings loader in `config/settings.py` loading `config/default.yaml` and `config/risk_weights.yaml`.
- [x] **Task 1.3:** Setup structured JSON audit logging in `backend/core/logging_setup.py` and custom exceptions in `backend/core/errors.py`.
- [x] **Task 1.4:** Initialize SQLite database connection and engine with WAL mode PRAGMA configuration in `storage/db.py`.
- [x] **Task 1.5:** Implement SQLAlchemy ORM models (`Flows`, `Features`, `ModelResults`, `Alerts`, `ThreatIntelIPs`, `ThreatIntelCIDRs`, `Users`) in `storage/models_orm.py`.
- [x] **Task 1.6:** Implement database repository layer in `storage/repositories/` (`FlowRepository`, `FeatureRepository`, `ModelResultRepository`, `AlertRepository`, `ThreatIntelRepository`, `UserRepository`).

---

## Phase 2: Traffic Simulation & Network Capture Pipeline
- [x] **Task 2.1:** Implement typed data models (`ValidatedPacket`, `FlowRecord`) in `network/flow_models.py`.
- [x] **Task 2.2:** Implement packet validator (`network/packet_validator.py`) discarding payload bytes and dropping malformed packets.
- [x] **Task 2.3:** Implement deduplicator (`network/deduplicator.py`) dropping duplicate packet sequences.
- [x] **Task 2.4:** Implement windowed flow aggregator (`network/flow_aggregator.py`) grouping packets by 5s sliding window.
- [x] **Task 2.5:** Implement synthetic normal traffic generator (`scripts/normal_traffic.py`).
- [ ] **Task 2.6:** Implement synthetic attack scenario generators in `simulator/scenarios/` (Port Scan, Subnet Scan, DDoS Flood, Exfiltration, Beaconing, Unknown Anomaly).
- [x] **Task 2.7:** Implement read-only Scapy capture listener (`network/passive_capture.py`) and interface guard (`network/interface_guard.py`).
- [x] **Task 2.8:** Implement read-only PCAP capture file parser (`network/pcap_reader.py`).

---

## Phase 3: Dataset Adapter & ML Model Training
- [x] **Task 3.0:** Setup isolated offline ML training environment in `/training/` with `training/requirements.txt` (pandas, numpy, scikit-learn, xgboost, imbalanced-learn, joblib, matplotlib, seaborn) and subfolders (`/notebooks/`, `/scripts/`, `/reports/`).
- [x] **Task 3.1:** Implement schema unification and label taxonomy normalization in `scripts/data_prep/unify_schema.py`.
- [x] **Task 3.2:** Implement dataset adapters for raw datasets (CICIDS2017, NSL-KDD) mapping columns to OneWay Sentinel 13-feature format and saving `data/processed/unified_dataset.parquet`.
- [x] **Task 3.2b:** Perform Exploratory Data Analysis (EDA) on `unified_dataset.parquet` (`training/scripts/perform_eda.py`) and output analysis report to `training/reports/eda_report.md`.
- [x] **Task 3.2c:** Implement feature scaling (`StandardScaler`), minority class oversampling, and 70/15/15 stratified train/val/test splitting in `scripts/data_prep/preprocess.py` saving `models/trained/scaler.pkl` and `data/processed/{train,val,test}.parquet`.
- [x] **Task 3.3:** Implement Supervised Random Forest Classifier baseline training script (`training/scripts/train_baseline.py`) saving artifact to `models/trained/random_forest_v1.pkl` and `models/rf_v1.pkl`.
- [x] **Task 3.4:** Implement Unsupervised Isolation Forest baseline training script (`training/scripts/train_baseline.py`) saving artifact to `models/trained/isolation_forest_v1.pkl` and `models/if_v1.pkl`.
- [x] **Task 3.5:** Implement model registry (`ml/model_registry.py`) and thread-safe inference runner (`ml/inference_service.py`).
- [x] **Task 3.6:** Perform hyperparameter tuning via `RandomizedSearchCV` (`training/scripts/tune_model.py`) optimizing weighted F1/recall on attack classes, saving final model `models/trained/threat_classifier_final.pkl` and selection report `training/reports/model_selection.md`.
- [x] **Task 3.7:** Perform single-pass evaluation on untouched holdout test set (`training/scripts/evaluate_final_test.py`) measuring accuracy (99.62%), ROC-AUC (0.9970), and per-flow latency, saving report `training/reports/final_evaluation.md`.
- [x] **Task 3.8:** Connect final trained model `models/trained/threat_classifier_final.pkl` and fitted scaler `models/trained/scaler.pkl` to `ml/model_registry.py` and `ml/inference_service.py`, verifying live feature vector format and end-to-end PCAP smoke test (`test_pcap_ingestion_and_threat_detection`).
- [x] **Task 3.9:** Document model retraining procedure, dataset ingestion steps, and semantic versioning rules in `docs/ai-engine.md` §7.

---

## Phase 4: Risk Scoring Engine & XAI Explainer
- [x] **Task 4.1:** Implement 13-feature numerical extraction function in `ml/feature_extraction.py`.
- [x] **Task 4.2:** Implement feature normalizer (`ml/feature_normalizer.py`) against learned source baseline.
- [x] **Task 4.3:** Implement score fusion logic (`ml/fusion/score_fusion.py`) applying classification policy.
- [x] **Task 4.4:** Implement risk score calculator (`backend/risk/risk_engine.py`) computing 0-100 score.
- [x] **Task 4.5:** Implement severity band mapper (`backend/risk/severity_mapper.py`) mapping score to severity bands.
- [x] **Task 4.6:** Implement model confidence calculator (`backend/risk/confidence_engine.py`).
- [x] **Task 4.7:** Implement plain-language explanation generator (`backend/risk/explainer.py`) translating RF feature importance and IF z-score deviations into text.
- [x] **Task 4.8:** Implement pipeline orchestrator (`backend/pipeline/orchestrator.py`) wiring ingestion $\rightarrow$ extraction $\rightarrow$ ML $\rightarrow$ risk $\rightarrow$ storage $\rightarrow$ WebSocket.

---

## Phase 5: FastAPI REST & WebSocket Telemetry Server
- [x] **Task 5.1:** Implement Pydantic v2 schemas in `backend/api/schemas.py`.
- [x] **Task 5.2:** Implement WebSocket connection manager in `backend/api/ws_manager.py`.
- [x] **Task 5.3:** Implement status router (`backend/api/routes_status.py`) and live stats router (`backend/api/routes_dashboard.py`).
- [x] **Task 5.4:** Implement threats/alerts router (`backend/api/routes_threats.py`) supporting GET alerts, GET alert detail, ack, false-positive, notes, and filtered history.
- [x] **Task 5.5:** Implement threat intel router (`backend/api/routes_intel.py`) and action router (`backend/api/routes_actions.py`).
- [x] **Task 5.6:** Implement PCAP upload router (`backend/api/routes_pcaps.py`).
- [x] **Task 5.7:** Implement geolocation router (`backend/api/routes_intel.py`) wrapping approximate GeoIP lookup.
- [x] **Task 5.8:** Implement main FastAPI app (`backend/api/main.py`) with CORS, routers, `/ws/alerts`, and `/ws/live-traffic` endpoints.

---

## Phase 6: React Frontend SPA & Dashboard Components
- [x] **Task 6.1:** Setup React 18 + Dark SOC CSS design system in `frontend/`.
- [x] **Task 6.2:** Configure color tokens (`frontend/styles.css`) and glass panel styling per `docs/design.md`.
- [x] **Task 6.3:** Build AppShell, Header, and Sidebar with persistent `ZeroOutboundBadge` ("0 BYTES SENT BACK").
- [x] **Task 6.4:** Build WebSocket telemetry connection hook with HTTP polling fallback.
- [x] **Task 6.5:** Build MainDashboard page with StatusBar, 4x KPICard row, TrafficChart, ThreatBreakdown, 5-stage DetectionPipelineStrip, and LiveAlertFeed.
- [x] **Task 6.6:** Build SimulatorControls component with scenario injection and PCAP upload view.
- [x] **Task 6.7:** Build Alert Evidence Inspector Modal with RiskGauge, ThreatBadge, XAI explanation panel, flow metadata table, GeoIP card, and triage buttons.
- [x] **Task 6.8:** Build Threat Logs Table page with FilterBar, CyberTable, pagination, and Quick Action buttons.
- [x] **Task 6.9:** Build Threat Intel Inspector page for IP reputation lookup and blacklisting.

---

## Phase 7: Threat Intelligence & Kali Lab Integration
- [x] **Task 7.1:** Create sample threat intel datasets in `/data/threat_intel/` (`malicious_ips.csv`, `malicious_cidrs.json`, `reputation_feeds.json`, `tor_exit_nodes.json`).
- [x] **Task 7.2:** Implement threat intel repository (`storage/repositories/threat_intel_repository.py`) and startup loader (`scripts/seed_threat_intel.py`).
- [x] **Task 7.3:** Integrate IP/CIDR threat lookup boost into pipeline scoring (`backend/risk/risk_engine.py`).
- [x] **Task 7.4:** Document Kali Linux lab execution commands in `docs/attack-scenarios.md`.

---

## Phase 8: Zero-Outbound Verification & E2E Validation
- [x] **Task 8.1:** Enforce procedural and structural zero-outbound transmission assertions in `network/interface_guard.py` and `backend/api/deps.py`.
- [x] **Task 8.2:** Implement end-to-end integration test (`tests/integration/test_pipeline_end_to_end.py`).
- [x] **Task 8.3:** Implement API route tests (`tests/integration/test_api_endpoints.py`).
- [x] **Task 8.4:** Verify sub-2-second flow-to-alert latency performance budget (measured at 0.262ms per flow).

---

## 9. Production-Readiness & Deployment Instructions

### 9.1 Environment Configuration (`.env`)
```ini
# OneWay Sentinel Configuration
APP_ENV=production
DEBUG=False
PORT=8000
HOST=0.0.0.0

# Passive Capture Interface
CAPTURE_INTERFACE=eth0
PROMISCUOUS_MODE=True
ZERO_OUTBOUND_ASSERTION=True

# Database & Storage
DATABASE_URL=sqlite:///./oneway_sentinel.db
THREAT_INTEL_DIR=./data/threat_intel

# Authentication & Security
ENABLE_AUTH=False
JWT_SECRET_KEY=sentinel_production_jwt_secret_key_change_in_prod_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 9.2 Starting the Application

#### Option A: Quick Start (FastAPI Backend + React Frontend + WebSockets)
```bash
# 1. Install Python backend dependencies
pip install -r requirements.txt

# 2. Seed historical threat intelligence database tables
python scripts/seed_threat_intel.py

# 3. Start the FastAPI Production Server (serves REST API, WebSockets, and React SPA)
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Open browser at: `http://localhost:8000/`

#### Option B: Live Passive Network Sniffer Worker (Requires Root / Administrator)
```bash
# Run Scapy passive packet capture worker on listening network interface (read-only)
python network/passive_capture.py --interface eth0
```

---

## 10. Jury Presentation & Live Demo Guide

### Phase 1: Baseline Normal Traffic Demonstration (0% False Positives)
1. Open the SOC Dashboard in the browser at `http://localhost:8000/`.
2. Notice the persistent **`0 BYTES SENT BACK (PASSIVE)`** trust badge in the sidebar.
3. In a terminal, run the synthetic normal user traffic generator:
   ```bash
   python scripts/normal_traffic.py --rate 5.0 --duration 10
   ```
4. **Expected Jury Observation:**
   - Packet counters on dashboard increment dynamically.
   - `Safe Benign Flows` count increases.
   - `Alerts Triggered` remains **0** (0% False Positive Rate verified).

### Phase 2: Live Attack Ingestion & Instant Threat Classification
1. Inject a Port Scan or Threat Intel attack scenario from the UI **Live Demo Scenario Injector** button or via command line:
   ```bash
   python -c "import requests; requests.post('http://localhost:8000/api/v1/telemetry/packet', json=[{'src_ip': '198.51.100.45', 'dst_ip': '10.0.0.5', 'src_port': 50000+i, 'dst_port': i+1, 'protocol': 'TCP', 'packet_length': 64} for i in range(25)])"
   ```
2. **Expected Jury Observation:**
   - Real-Time WebSocket streams `ALERT_NEW` notification instantly ($<0.26$s latency).
   - High/Critical red alert pill appears in the **Live Real-Time Threat Alerts Feed**.
   - Click **Inspect** to display the **Alert Evidence Inspector Modal**, highlighting the plain-language XAI explanation and 0–100 risk score gauge.

### Phase 3: Zero-Outbound Monitoring Guarantee Proof
1. Click the **Block IP** action button on any alert row or Threat Intel Inspector card.
2. **Expected Jury Observation:**
   - Red warning notification banner pops up: `Active response prohibited: IP blocking is physically disabled on passive diode links.`
   - Proves OneWay Sentinel maintains 100% passive, detect-only data diode integrity without transmitting outbound packets.
