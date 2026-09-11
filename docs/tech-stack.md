# OneWay Sentinel — Technology Stack Specification (`tech-stack.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`master-prd.md`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/master-prd.md), [`architecture.md`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md), and [`rules.md`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md).

---

## 1. Core Architecture & Language Standard

OneWay Sentinel is constructed as a **modular monolith** running on a single host (commodity student laptop or monitoring station). A single core Python runtime powers ingestion, feature extraction, ML inference, risk scoring, persistence, and REST/WebSocket API serving. A companion React SPA provides real-time security monitoring.

- **Primary Language:** Python 3.11+ (Backend, ML, Ingestion, Storage, Scripts).
- **Frontend Language:** JavaScript (ES6+) / React 18.
- **Concurrency Model:** Async IO (`asyncio`) for network ingestion, pipeline queuing, and WebSocket broadcasting; multi-threading / daemon tasks for synthetic traffic simulation and passive packet capture loops.

---

## 2. Technology Stack Breakdown

| Layer | Component / Tool | Version / Library | Purpose & Rationale | Constraints & Prohibitions |
|---|---|---|---|---|
| **Backend Runtime** | Python | 3.11+ | Single language across ML, network data structures, and web API (PRD §19). | No multi-language microservices. |
| **API Framework** | FastAPI | 0.109+ | High-performance, async-native REST framework with automatic OpenAPI spec generation and native WebSockets. | Handlers must delegate business logic to pipeline/repositories. |
| **ASGI Server** | Uvicorn | 0.27+ | Lightning-fast ASGI server implementation for hosting FastAPI and managing async client sockets. | Single-process production/demo deployment. |
| **Data Validation** | Pydantic | v2.6+ | Typed schema definitions for all API requests, responses, configuration objects, and internal pipeline data structures. | No untyped dictionaries crossing module boundaries. |
| **Configuration** | Pydantic Settings | v2.1+ | Centralized environment variable and YAML file settings management (`config/settings.py`). | Secrets/keys must never be committed to source. |
| **Packet Ingestion** | Scapy | 2.5+ | Passive packet header extraction (`AsyncSniffer`), PCAP file parsing (`rdpcap`). | **STRICTLY PROHIBITED:** `send`, `sendp`, `sr`, `sr1`, raw socket writes. |
| **ML Models** | scikit-learn | 1.4+ | `RandomForestClassifier` (supervised classification) and `IsolationForest` (unsupervised anomaly detection). | **NO Deep Learning frameworks** (PyTorch/TensorFlow unnecessary for tabular flow metadata). |
| **Model Persistence**| joblib | 1.3+ | Serialization and deserialization of trained sklearn models (`.pkl` format). | Models must load via `ml/model_registry.py` only. |
| **Data Processing** | pandas / numpy | 2.2+ / 1.26+ | Fast tabular manipulation for feature extraction, baseline normalization, and dataset adapters. | Used only in `ml/` and `datasets/`, not packet validator. |
| **Database ORM** | SQLAlchemy | 2.0+ | Modern async/sync ORM and SQL expression builder for SQLite persistence. | SQL queries written only in `storage/repositories/`. |
| **Database Engine** | SQLite3 | 3.45+ (WAL mode) | Zero-ops, single-file relational storage with Write-Ahead Logging (WAL) for concurrent read/write access. | **NO packet payload storage**; metadata only. |
| **GeoIP Lookup** | MaxMind GeoLite2 | `geoip2` 4.8+ | Offline binary `.mmdb` database for IP to Country/City lookups without external network dependencies. | **MUST** flag output as `is_approximate: true`. |
| **Frontend Framework**| React | 18.2+ | Component-driven UI library for the SOC security dashboard SPA. | Functional components and hooks only. |
| **Build Tool** | Vite | 5.0+ | Fast HMR development server and optimized production bundler for React. | Pre-configured dev proxy to FastAPI backend (`:8000`). |
| **Styling System** | Tailwind CSS | 3.4+ | Utility-first CSS framework configured with custom tokens from `design.md`. | Compose shared `.cyber-*` classes via `@layer components`. |
| **Data Visualization**| Recharts | 2.12+ | React charting library for live volume line charts and threat breakdown donut charts. | One visual glow per element maximum. |
| **Iconography** | Lucide React | 0.330+ | Clean stroke-based technical icon set. | Icons must always pair with visible/accessible text. |
| **Testing** | pytest & RTL | pytest 8.0+ / RTL | Comprehensive test suite covering unit math, ML deterministic inference, API routes, and zero-outbound verification. | `verify_zero_outbound.py` must pass on all code changes. |

---

## 3. Asynchronous Pipeline & Threading Architecture

To prevent CPU-bound Scapy capture loops or thread blocking from freezing the main FastAPI event loop, the system enforces a strict threading boundary:

```
┌─────────────────────────────────────────────────────────────┐
│                       THREAD BOUNDARY                       │
│                                                             │
│  [ Scapy AsyncSniffer Thread ] / [ Synthetic Simulator ]   │
│                             │                               │
│                             ▼                               │
│                   Thread-Safe Data Queue                    │
│            (janus.Queue / loop.call_soon_threadsafe)        │
│                             │                               │
│                             ▼                               │
│            [ FastAPI Main Async Event Loop ]                │
│                             │                               │
│          Feature Extraction ──► Hybrid ML Scoring           │
│                             │                               │
│              Risk Engine ──► SQLite Persistence             │
│                             │                               │
│                             ▼                               │
│               WebSocket Manager (/ws/alerts)                │
└─────────────────────────────────────────────────────────────┘
```

1. **Packet Capture Thread:** `network/passive_capture.py` operates Scapy in a background thread. Header metadata is parsed into `ValidatedPacket` objects.
2. **Thread-Safe Queueing:** `ValidatedPacket` objects are passed into an `asyncio.Queue` using `loop.call_soon_threadsafe()`.
3. **Pipeline Processing:** `backend/pipeline/orchestrator.py` consumes the queue asynchronously, performing flow aggregation, feature extraction, ML scoring, risk engine calculations, and SQLite persistence.
4. **WebSocket Push:** Broadcast events are pushed to connected dashboard clients over `/ws/alerts`.

---

## 4. Safety, Memory & Performance Guarantees

1. **Immediate Payload Disposal:** `network/packet_validator.py` discards raw packet payloads immediately after extracting standard IP/TCP/UDP header fields (`src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `packet_length`, `timestamp`). No payload bytes are ever buffered or persisted.
2. **Buffer Overflow & Memory Capping:** Flow windows strictly cap stored packet metadata to 5-second sliding windows (configurable via `config/default.yaml`).
3. **Zero Outbound Enforcement:** `network/interface_guard.py` checks socket creation parameters. Any attempt to instantiate a socket with write capability on the capture interface triggers an immediate system panic.
