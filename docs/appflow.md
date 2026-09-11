# appflow.md — OneWay Sentinel Application Flow

*Generated from `prd.md` (Master PRD — OneWay Sentinel, SIH26145) and `architecture.md` (OneWay Sentinel — Complete System Architecture). This document is a synthesis; it introduces no functionality beyond what those two files specify. Every unresolved gap or conflict between them is documented in Section 22.*

---

## 1. Application Flow Overview

**What the application does:** OneWay Sentinel is a passive, AI-powered monitoring system that sits on the output side of a data diode (or a SPAN/mirror tap) and detects known attack patterns and unknown/covert-channel anomalies in unidirectional IP traffic, using only flow metadata (never payload), and **never transmits anything back through the monitored link**. A hybrid ML pipeline (Random Forest + Isolation Forest) scores every flow 0–100, bands it into a severity level, and generates a plain-language explanation for every qualifying alert, all surfaced on a live web dashboard.

**Primary user roles** (per PRD §4 — see Section 4 for the important caveat about how these map to actual system access):
- SOC / Duty Analyst
- Network Administrator
- Security Team Lead / Manager
- Deploying Organization (institutional stakeholder, not a distinct interactive role)
- Presenter / Demo User (PRD §21 user story; operates the simulator during a live demo)

**Main objective:** Prove that real-time, explainable threat detection is achievable using one-way flow metadata alone, with zero return traffic, on a single laptop.

**High-level user journey:** A user opens the dashboard, sees system/passive status and live traffic statistics, watches alerts appear in real time (or triggers them via the simulator for a demo), opens an alert to see its evidence and explanation, and either acknowledges it or marks it a false positive. A security lead separately reviews historical alerts through filtering.

**Major functional areas:**
1. Live monitoring (status, traffic volume, threat/safe breakdown)
2. Alerting (live feed, detail view, triage actions)
3. Historical review (searchable/filterable alert history)
4. Demo/simulation control (start baseline traffic, inject attack scenarios)
5. Offline analysis via PCAP upload (P1)
6. Network relationship visualization (P2)

**High-level flow:**

```
User (SOC Analyst / Admin / Lead / Presenter)
 ↓
Entry → Dashboard URL (no login gate in MVP — see §22 [ARCHITECTURE GAP])
 ↓
MainDashboard loads
 ↓
Live Status + Traffic Chart + Threat Breakdown + Alert Feed (WS: /ws/alerts)
 ↓
[Optional] Simulator Controls → inject baseline/attack traffic
 ↓
Ingestion (live capture / simulator / PCAP) → Feature Extraction → Hybrid ML Scoring
 ↓
Risk Engine → Severity Banding → Explanation Generator
 ↓
Storage (SQLite: flows, features, model_results, alerts)
 ↓
WebSocket AlertEvent → Dashboard live update
 ↓
User opens AlertDetail → reviews evidence → Acknowledge / False Positive / Notes
 ↓
User (Security Lead) → AlertHistory → filters by time/category/severity/source IP
```

---

## 2. User Roles and Permissions

| Role | Description | Main Capabilities | Restricted Areas |
|---|---|---|---|
| **SOC / Duty Analyst** | Front-line operator watching the live link | View MainDashboard, view LiveAlertFeed, open AlertDetail, Acknowledge/Mark False Positive/Add Notes, view AlertHistory | None enforced by the system — see gap below |
| **Network Administrator** | Confirms anomalies are genuine vs. misconfiguration | Same dashboard access as Analyst; primary consumer of `ZeroOutboundBadge` / `/api/status` as a trust signal | None enforced by the system |
| **Security Team Lead / Manager** | Reviews trends, audits analyst actions | AlertHistory with filtering (date, category, severity, source IP, status); same alert-detail and triage actions as an Analyst | None enforced by the system |
| **Deploying Organization** | Institutional stakeholder, not a hands-on dashboard user | N/A — represented through the system's non-functional guarantees (zero return traffic), not through a UI role | N/A |
| **Presenter / Demo User** «[ASSUMPTION]» — PRD §21 implies this role but PRD §4 does not list it in the stakeholder table | Runs the SIH live demo | `SimulatorControls` (start normal traffic, trigger a named attack scenario), all Analyst capabilities | None enforced by the system |

**«[ARCHITECTURE GAP]»** Neither `prd.md` nor `architecture.md` defines role-based access control for the MVP. `architecture.md` §20/§21 lists "authentication on the API" as a **P2** item and explicitly designs it as toggleable middleware that "never blocks or destabilizes P0." Until that P2 work lands, **every user who can reach the dashboard has identical capabilities** — there is no technical distinction between an Analyst, an Administrator, or a Lead; the "roles" above are organizational/functional, not access-controlled. The Feature Priority Matrix (PRD §24) confirms "Dashboard authentication" is P2, consistent with this.

---

## 3. Application Navigation Map

```
OneWay Sentinel (SPA)
│
├── (No Authentication screens in MVP — P2 only, undesigned; see §22)
│
├── MainDashboard  [P0]  — default/landing route
│   ├── StatusBar (incl. ZeroOutboundBadge)
│   ├── TrafficChart
│   ├── ThreatBreakdown
│   ├── LiveAlertFeed  → click alert → AlertDetail
│   └── SimulatorControls (start/stop normal traffic; start/stop a named attack scenario)
│       └── PCAP Upload «[ASSUMPTION]» — no dedicated frontend component is named in
│           architecture.md's folder tree for the POST /api/pcap/upload route; assumed to be
│           surfaced as a control within SimulatorControls or a modal on MainDashboard.
│
├── AlertDetail  [P0 basic / P1 enriched]  — reached from LiveAlertFeed or AlertHistory row
│   ├── Full flow metadata, risk score, severity, explanation, category
│   ├── Approximate Location (geolocation, P1)
│   └── Recent history for that source IP (P1)
│
├── AlertHistory  [P0 basic / P1 full]
│   ├── FilterBar (date range, category, severity, source IP, status)
│   └── Alert table (Time | Source IP | Category | Score | Status) → click row → AlertDetail
│
└── NetworkGraph  [P2]  — source→destination node/edge view, color = risk, edge width = volume
```

Only screens with a corresponding page component in `architecture.md` §3 (`frontend/src/pages/`) are listed as top-level navigation destinations; `SimulatorControls`, `StatusBar`, `TrafficChart`, `ThreatBreakdown`, `LiveAlertFeed`, and `FilterBar` are components embedded within those pages, per `architecture.md` §3 and §12.

---

## 4. Screen-by-Screen Application Flow

### Screen: MainDashboard

**Purpose:** Single real-time view of link health and active threats (PRD §6.6, §11; `frontend/src/pages/MainDashboard.jsx`).

**User Role:** All users (no access restriction enforced — §2).

**Entry Points:** Application root URL; default landing screen; navigated back to from AlertDetail or AlertHistory.

**Exit Points:** Click an alert in LiveAlertFeed → AlertDetail. Navigate to AlertHistory or NetworkGraph (navigation mechanism between pages is «[ARCHITECTURE GAP]» — no router/nav-bar component is named in `architecture.md`'s frontend folder tree; a top-level nav is «[ASSUMPTION]»).

**UI Components:**

| Component | Type | Purpose | Data Source | User Interaction |
|---|---|---|---|---|
| StatusBar (incl. `ZeroOutboundBadge`) | Status indicator | Shows system/listening/degraded status and the "0 bytes sent back" trust signal (PRD §11, FR-018) | `GET /api/status` | None (read-only) |
| Counters (packets/flows scanned, threats detected, safe traffic) | Stat cards | Live volumetric overview | `GET /api/stats/live`, refreshed via `/ws/alerts` push | None (read-only) |
| TrafficChart | Line chart | Live traffic-volume over time (PRD §11) | `/ws/alerts` stream + `/api/stats/live` | None (read-only) |
| ThreatBreakdown | Donut/breakdown chart | Threat-vs-safe and category breakdown | `/ws/alerts` stream + `/api/stats/live` | None (read-only) |
| LiveAlertFeed | Live list | Most recent alerts, severity color-coded | `/ws/alerts` push (real-time) | Click an alert → navigates to AlertDetail |
| SimulatorControls | Button panel | Start/stop baseline traffic; trigger a named attack scenario for the demo | User-initiated | Click "Start Normal Traffic" / select + start a scenario / stop |

**User Actions:**

*Action: Load dashboard*
```
User opens app
 ↓ Frontend Validation: none (no input)
 ↓ API Request: GET /api/status, GET /api/stats/live; WS connect to /ws/alerts
 ↓ Backend Service: backend/api routes_status.py, routes_alerts.py, ws_manager.py
 ↓ Database / Processing: storage/repositories (flow_repository, alert_repository)
 ↓ API Response: current status + stats JSON; ongoing WS stream of AlertEvent JSON
 ↓ Frontend State Update: React context/WS reducer (architecture.md §12) populates counters/charts/feed
 ↓ UI Feedback: StatusBar shows live/degraded; charts and feed populate as events arrive
```

*Action: Start normal-traffic simulator*
```
User clicks "Start Normal Traffic" in SimulatorControls
 ↓ Frontend Validation: none
 ↓ API Request: POST /api/simulator/normal/start
 ↓ Backend Service: routes_simulator.py → simulator/normal_traffic_simulator.py
 ↓ Database / External Service: simulator pushes synthetic FlowRecord events into the same
   ingestion queue backend/pipeline/orchestrator.py consumes (architecture.md §13)
 ↓ Processing: full pipeline (feature extraction → hybrid ML → risk → storage → WS broadcast)
 ↓ API Response: 200 OK (simulator running); subsequent flows arrive via /ws/alerts, not the
   POST response itself
 ↓ Frontend State Update: TrafficChart/ThreatBreakdown counters begin climbing
 ↓ UI Feedback: "safe traffic climbing" per the demo sequence (architecture.md §23, step 2)
```

*Action: Trigger an attack scenario*
```
User selects a scenario (port scan / network scan / DDoS-like flood / exfiltration /
beaconing / unknown anomaly — PRD §9) and clicks "Start"
 ↓ Frontend Validation: a scenario must be selected
 ↓ API Request: POST /api/simulator/attack/{scenario}/start
 ↓ Backend Service: routes_simulator.py → simulator/attack_simulator.py + simulator/scenarios/*.py
 ↓ Database / External Service: scenario emitter pushes shaped synthetic flow events into the
   ingestion queue
 ↓ Processing: identical pipeline as live traffic — feature extraction, RF + IF scoring, fusion,
   risk scoring, explanation
 ↓ API Response: 200 OK
 ↓ Frontend State Update: LiveAlertFeed receives a new AlertEvent via /ws/alerts, generally
   within 2 seconds (PRD FR-020, success metric target)
 ↓ UI Feedback: new alert appears, color-coded by severity; user story acceptance criterion is
   "a visible alert on the dashboard within 2 seconds" (PRD §21)
```

*Action: PCAP upload* «[ASSUMPTION]» — placement and exact frontend flow are not specified; endpoint is defined.
```
User uploads a .pcap file
 ↓ Frontend Validation: file type «[ASSUMPTION — not specified]»
 ↓ API Request: POST /api/pcap/upload
 ↓ Backend Service: routes_pcap.py → network/pcap_reader.py (scapy.rdpcap, read-only) →
   backend/pipeline/orchestrator.py
 ↓ Database / Processing: same feature extraction / hybrid ML / risk / storage pipeline as live
   traffic (PRD §6.8, FR-003)
 ↓ API Response: «[RESPONSE SCHEMA NOT SPECIFIED]»
 ↓ Frontend State Update: resulting flows/alerts appear identically to live-sourced ones
   (flows table `source` column stores `'pcap'`)
 ↓ UI Feedback: «[ASSUMPTION — not specified: progress indicator, completion toast, etc.]»
```

**Navigation:**
- Click an item in LiveAlertFeed → `GET /api/alerts/{id}` → open AlertDetail → passes `alert_id`.
- Navigate to AlertHistory: mechanism not specified — «[ARCHITECTURE GAP]».
- Navigate to NetworkGraph (P2): mechanism not specified — «[ARCHITECTURE GAP]».

---

### Screen: AlertDetail

**Purpose:** Let an analyst understand exactly why a flow was flagged and review its full evidence (PRD §6.5, §11; `frontend/src/pages/AlertDetail.jsx`).

**User Role:** All users.

**Entry Points:** Click from LiveAlertFeed (MainDashboard) or a row in AlertHistory. Both pass the alert's ID.

**Exit Points:** Back to MainDashboard or AlertHistory (navigation mechanism unspecified — «[ARCHITECTURE GAP]»).

**UI Components:**

| Component | Type | Purpose | Data Source | User Interaction |
|---|---|---|---|---|
| Full flow metadata panel | Detail table | Source/destination IP, ports, protocol, timing, volume | `GET /api/alerts/{id}` | Read-only |
| Risk score + severity | Status indicator | 0–100 score and severity band | `GET /api/alerts/{id}` | Read-only |
| Threat category label | Badge | Named category or "Unknown Anomaly" | `GET /api/alerts/{id}` | Read-only |
| Plain-language explanation | Text block | 2–3 line explanation naming top contributing features (PRD §6.5) | `GET /api/alerts/{id}` (`backend/risk/explainer.py` output) | Read-only |
| Approximate Location (P1) | Text/badge | Geolocation of source IP, always labeled "Approximate Location," never attacker attribution | `GET /api/geolocation/{ip}` | Read-only |
| Recent source history (P1) | Mini list/table | Recent alerts from the same source IP | «[API ENDPOINT NOT SPECIFIED IN ARCHITECTURE]» — `architecture.md` §12 describes this as "queried by src_ip" but does not name a route for it | Read-only |
| Acknowledge / False Positive / Add Notes | Buttons + text field | Triage actions (PRD §12) | User input | Click / type + submit |

**User Actions:**

*Action: Acknowledge alert*
```
User clicks "Acknowledge"
 ↓ Frontend Validation: alert must be in a state allowing this action «[ASSUMPTION on exact
   allowed prior states — see §22 CONFLICT on alert lifecycle]»
 ↓ API Request: POST /api/alerts/{id}/ack
 ↓ Backend Service: routes_alerts.py → storage/repositories/alert_repository.py
 ↓ Database: alerts.status updated to 'acknowledged'
 ↓ API Response: «[RESPONSE SCHEMA NOT SPECIFIED]»
 ↓ Frontend State Update: alert status badge updates
 ↓ UI Feedback: confirmation «[ASSUMPTION — not specified: toast vs. inline update]»
```

*Action: Mark as False Positive*
```
User clicks "Mark as False Positive"
 ↓ Frontend Validation: none specified
 ↓ API Request: POST /api/alerts/{id}/false-positive
 ↓ Backend Service: routes_alerts.py → alert_repository.py
 ↓ Database: alerts.status updated to 'false_positive'
 ↓ API Response: «[RESPONSE SCHEMA NOT SPECIFIED]»
 ↓ Frontend State Update: alert removed from or re-styled within the active LiveAlertFeed
   ("keep the active alert list focused on real threats" — PRD §21 user story)
 ↓ UI Feedback: status updates
```

*Action: Add Notes*
```
User types a note and submits
 ↓ Frontend Validation: none specified
 ↓ API Request: POST /api/alerts/{id}/notes
 ↓ Backend Service: routes_alerts.py → alert_repository.py
 ↓ Database: alerts.notes updated
 ↓ API Response: «[RESPONSE SCHEMA NOT SPECIFIED]»
 ↓ Frontend State Update: note appears in detail view
 ↓ UI Feedback: «[ASSUMPTION — not specified]»
```

**Navigation:**
- No further forward navigation specified from AlertDetail beyond source-history links, whose target/behavior is «[ARCHITECTURE GAP]».

---

### Screen: AlertHistory

**Purpose:** Durable, searchable record of past alerts for review, reporting, and trend spotting (PRD §6.7, §11; `frontend/src/pages/AlertHistory.jsx`).

**User Role:** All users; primary named consumer is the Security Team Lead (PRD §4, §21 UC6).

**Entry Points:** From MainDashboard (mechanism unspecified) or directly if the app supports deep links (unspecified).

**Exit Points:** Click a row → AlertDetail, passing the alert ID.

**UI Components:**

| Component | Type | Purpose | Data Source | User Interaction |
|---|---|---|---|---|
| FilterBar | Form controls | Filter by date range, category, severity, source IP, status (PRD §6.7, §11) | User input | Select/type filter values, apply |
| Alert table | Data table | Columns: Time \| Source IP \| Category \| Score \| Status (PRD §11) | `GET /api/alerts/history` | Click row → AlertDetail |
| Row actions | Inline buttons | Acknowledge / False Positive / Notes directly from the table (`architecture.md` §12) | User input | Click, calls the same endpoints as AlertDetail |

**User Actions:**

*Action: Apply filters*
```
User sets filter values and applies
 ↓ Frontend Validation: date-range validity «[ASSUMPTION]»
 ↓ API Request: GET /api/alerts/history (with query parameters for date range, category,
   severity, source IP, status — exact query-param schema «[REQUEST SCHEMA NOT SPECIFIED]»)
 ↓ Backend Service: routes_alerts.py → alert_repository.py
 ↓ Database: SQLite `alerts` table, filtered query
 ↓ API Response: filtered alert list «[RESPONSE SCHEMA NOT SPECIFIED]»
 ↓ Frontend State Update: table re-renders with filtered results
 ↓ UI Feedback: table updates; if empty, an empty state is shown (see §15)
```

*Action: Row-level Acknowledge / False Positive / Notes* — identical flow to the equivalent AlertDetail actions in Section 4 above, invoked directly from the table row.

**Navigation:**
- Click row → `GET /api/alerts/{id}` → AlertDetail, passing `alert_id`.

---

### Screen: NetworkGraph (P2)

**Purpose:** At-a-glance view of which source IPs are talking to which destinations and at what risk level (PRD §6.10, §11; `frontend/src/pages/NetworkGraph.jsx`).

**User Role:** All users.

**Entry Points:** From MainDashboard (mechanism unspecified — «[ARCHITECTURE GAP]»).

**Exit Points:** Back to MainDashboard (unspecified).

**UI Components:**

| Component | Type | Purpose | Data Source | User Interaction |
|---|---|---|---|---|
| Node/edge graph | Interactive visualization | Node color = risk, edge thickness = traffic volume (PRD §6.10, §11) | Aggregated flow/alert data — «[API ENDPOINT NOT SPECIFIED IN ARCHITECTURE]» (no `/api/graph` or similar route exists in the §11 API table) | Presumably click/hover for detail — «[ASSUMPTION, not specified]» |

This entire screen is **P2** (PRD §24 priority matrix; `architecture.md` §20 P2 list), decoupled so it doesn't block P0/P1 delivery.

---

## 5. End-to-End User Journeys

### Journey: UC1 — Detect Port/Network Scan

**Actor:** SOC Analyst (passive observer of the result), Presenter (trigger, in demo mode).

**Preconditions:** Ingestion pipeline running (live, simulator, or PCAP); dashboard connected to `/ws/alerts`.

**Main Flow:**
1. Traffic exhibiting high port/destination diversity from a single source arrives (live capture, or the Presenter starts the port-scan scenario via SimulatorControls).
2. `network/flow_aggregator.py` groups packets into a flow keyed by (src_ip, dst_ip, src_port, dst_port, protocol) over the sliding window.
3. `ml/feature_extraction.py` computes the feature vector, including `unique_dst_port_count`.
4. Random Forest and Isolation Forest both score the flow; fusion applies PRD/architecture §7 policy.
5. `backend/risk/risk_engine.py` computes a 0–100 score; `severity_mapper.py` bands it Medium–High (PRD §9).
6. `explainer.py` generates an explanation citing port diversity.
7. Alert is persisted (`alerts` table) and broadcast over `/ws/alerts`.
8. Dashboard's LiveAlertFeed shows the new alert, severity color-coded.
9. Analyst clicks the alert → AlertDetail shows full evidence and explanation.

**Alternative Flows:** Traffic arrives via PCAP upload instead of live/simulator — same pipeline from step 2 onward (PRD §6.8).

**Failure Flows:** See Section 14 (Error and Edge-Case Flows) for ML-unavailable, storage, and network-failure paths, which apply identically to every journey in this section.

**Final State:** A Medium–High severity alert with category "Port Scanning" (or "Network/Host Scanning") is visible in LiveAlertFeed and AlertHistory, with a plain-language explanation.

---

### Journey: UC2 — Detect Volumetric Flood

**Actor:** SOC Analyst / Presenter.

**Preconditions:** Same as UC1.

**Main Flow:**
1. High packet rate with low, uniform inter-arrival time arrives (live/simulator DDoS-like scenario).
2. Pipeline stages proceed as in UC1 steps 2–7.
3. Risk score maps to **Critical** severity (PRD §9, §12: 80–100 band).
4. Alert appears in LiveAlertFeed with Critical color-coding, target latency under 2 seconds (PRD FR-020, success metric).

**Alternative Flows:** None specified beyond source (live vs. simulator vs. PCAP).

**Failure Flows:** See Section 14.

**Final State:** A Critical-severity, "DDoS-like Volumetric Behavior" alert is visible and persisted.

---

### Journey: UC3 — Detect Exfiltration-style Volume Anomaly

**Actor:** SOC Analyst / Presenter.

**Preconditions:** A learned per-source baseline exists (models pre-trained offline per PRD §7/§16 and `architecture.md` §22 step 6).

**Main Flow:**
1. A source's outbound byte count spikes far above its learned baseline (live/simulator exfiltration scenario).
2. Feature engineering normalizes raw counts against the per-source baseline (PRD §7).
3. Pipeline stages proceed as in UC1.
4. Risk score maps to **Critical** severity (PRD §9).
5. Alert appears in LiveAlertFeed and is persisted with category "Data Exfiltration."

**Alternative Flows:** None specified.

**Failure Flows:** See Section 14.

**Final State:** A Critical-severity "Data Exfiltration" alert is visible with an explanation citing the volume deviation.

---

### Journey: UC4 — Detect Unknown/Covert-Channel Anomaly

**Actor:** SOC Analyst / Presenter.

**Preconditions:** Isolation Forest model trained on benign flows is loaded (`models/trained/isolation_forest_v1.pkl`).

**Main Flow:**
1. Traffic doesn't match a known RF category but deviates statistically from baseline (live/simulator beaconing or unknown-anomaly scenario).
2. Feature extraction and dual-model scoring proceed as in UC1.
3. Fusion policy (`architecture.md` §7): RF confidence for a known class is below threshold, but IF anomaly score exceeds its threshold → labeled "Unknown Anomaly" (or "Beaconing" if evidence supports a more specific label, per PRD §9).
4. `explainer.py` generates an explanation from the anomaly-model deviation (z-score from per-source baseline).
5. Alert persisted and broadcast; severity per score (PRD §9).

**Alternative Flows:** If RF confidence for a specific class (e.g., Beaconing) does clear the threshold, the alert is labeled with that specific category instead of "Unknown Anomaly."

**Failure Flows:** See Section 14.

**Final State:** An "Unknown Anomaly" (or specific-category) alert appears with severity per score and an anomaly-based explanation. Per the SIH demo sequence (`architecture.md` §23 step 5), this is explicitly called out as "shown as Unknown Anomaly if RF confidence is insufficient."

---

### Journey: UC5 — Investigate an Alert

**Actor:** SOC Analyst.

**Preconditions:** At least one alert exists in LiveAlertFeed or AlertHistory.

**Main Flow:**
1. Analyst opens the dashboard (MainDashboard) or AlertHistory.
2. Analyst clicks an alert → `GET /api/alerts/{id}` → AlertDetail opens with flow metadata, score, and explanation (PRD §21 UC5).
3. Analyst reviews the evidence (feature values, explanation, approximate location if P1 is implemented).
4. Analyst clicks Acknowledge or Mark as False Positive.
5. `POST /api/alerts/{id}/ack` or `POST /api/alerts/{id}/false-positive` updates `alerts.status`.
6. UI reflects the new status.

**Alternative Flows:** Analyst adds Notes instead of, or in addition to, Acknowledge/False Positive (`POST /api/alerts/{id}/notes`).

**Failure Flows:**
- Invalid alert ID → «[RESPONSE SCHEMA NOT SPECIFIED]», but `architecture.md` §19 confirms this error path is covered by API tests ("error paths (invalid alert id...)").
- Network failure during the POST → «[ASSUMPTION — not specified: retry, error toast]».

**Final State:** Alert status is updated to `acknowledged` or `false_positive` in the database and reflected in the UI; if marked false positive, it no longer contributes to the active-alert view per PRD §21's stated intent.

---

### Journey: UC6 — Review Historical Trends

**Actor:** Security Team Lead.

**Preconditions:** Historical alert data exists in the `alerts` table.

**Main Flow:**
1. Lead navigates to AlertHistory.
2. Lead sets filters (date range, category, severity, source IP, status) via FilterBar.
3. Frontend sends `GET /api/alerts/history` with the filter parameters.
4. `alert_repository.py` queries SQLite and returns matching rows.
5. Table renders: Time | Source IP | Category | Score | Status.
6. Lead clicks a row to open AlertDetail for deeper review (→ UC5 flow).

**Alternative Flows:** No filters applied → full history returned (subject to any default pagination, which is «[ARCHITECTURE GAP — not specified]»).

**Failure Flows:** Empty result set → empty state (Section 15). Backend/database failure → error state (Section 14).

**Final State:** Lead sees a filtered table of historical alerts matching the chosen criteria.

---

### Journey: UC7 — Offline Analysis via PCAP (P1)

**Actor:** Any dashboard user (analyst, presenter, or a judge bringing their own sample per PRD §6.8).

**Preconditions:** A `.pcap` file is available for upload.

**Main Flow:**
1. User uploads a PCAP file «[ASSUMPTION on exact UI location — see Section 4]».
2. `POST /api/pcap/upload` → `routes_pcap.py` → `network/pcap_reader.py` reads the file (read-only, `scapy.rdpcap`, never re-injected onto a live interface — `architecture.md` §8).
3. Parsed packets are converted into the same `FlowRecord` shape and pushed into the identical ingestion queue as live/simulator traffic (`architecture.md` §8 Mode B).
4. Full pipeline (feature extraction → hybrid ML → risk → storage → WS broadcast) runs identically to live traffic (PRD §6.8, FR-003).
5. Resulting flows/alerts appear in LiveAlertFeed and AlertHistory, with `flows.source = 'pcap'`.

**Alternative Flows:** None specified.

**Failure Flows:** Malformed PCAP upload is explicitly covered as a test case in `architecture.md` §19 ("malformed PCAP upload") but the resulting user-facing behavior is «[RESPONSE SCHEMA NOT SPECIFIED]».

**Final State:** Same scored-flow/alert output as the live path (PRD §6.8), visible on the dashboard.

---

## 6. Frontend → Backend → Data Flow

| UI Screen | User Action | Frontend Component | API/Service | Backend Component | Database/Data Source | Response | UI Result |
|---|---|---|---|---|---|---|---|
| MainDashboard | Page load | `MainDashboard.jsx`, `StatusBar.jsx` | `GET /api/status` | `routes_status.py` | — | Status JSON | StatusBar + ZeroOutboundBadge render |
| MainDashboard | Page load | `MainDashboard.jsx` | `GET /api/stats/live` | `routes_alerts.py` (or a stats-specific handler — router not named beyond the route table) | `flows`, `alerts` tables | Stats JSON | Counters, TrafficChart, ThreatBreakdown populate |
| MainDashboard | Live updates | `LiveAlertFeed.jsx` | `WS /ws/alerts` | `ws_manager.py`, `backend/pipeline/orchestrator.py` | `alerts` table (post-persist) | AlertEvent JSON stream | Feed, charts, counters update live |
| MainDashboard | Start normal traffic | `SimulatorControls.jsx` | `POST /api/simulator/normal/start` | `routes_simulator.py` → `simulator/normal_traffic_simulator.py` | Ingestion queue | 200 OK | Traffic begins flowing into pipeline |
| MainDashboard | Trigger attack scenario | `SimulatorControls.jsx` | `POST /api/simulator/attack/{scenario}/start` | `routes_simulator.py` → `simulator/attack_simulator.py` + `scenarios/*.py` | Ingestion queue | 200 OK | Alert appears via WS within ~2s |
| MainDashboard | Upload PCAP | «[ASSUMPTION component]» | `POST /api/pcap/upload` | `routes_pcap.py` → `network/pcap_reader.py` | Ingestion queue | «[RESPONSE SCHEMA NOT SPECIFIED]» | Resulting alerts appear via WS |
| LiveAlertFeed / AlertHistory | Click alert | — | `GET /api/alerts/{id}` | `routes_alerts.py` → `alert_repository.py` | `alerts`, `flows`, `features`, `model_results` tables | Full alert record | AlertDetail renders |
| AlertDetail | Acknowledge | `AlertDetail.jsx` | `POST /api/alerts/{id}/ack` | `routes_alerts.py` → `alert_repository.py` | `alerts.status` updated | «[RESPONSE SCHEMA NOT SPECIFIED]» | Status badge updates |
| AlertDetail | Mark False Positive | `AlertDetail.jsx` | `POST /api/alerts/{id}/false-positive` | `routes_alerts.py` → `alert_repository.py` | `alerts.status` updated | «[RESPONSE SCHEMA NOT SPECIFIED]» | Alert re-styled/removed from active view |
| AlertDetail | Add Notes | `AlertDetail.jsx` | `POST /api/alerts/{id}/notes` | `routes_alerts.py` → `alert_repository.py` | `alerts.notes` updated | «[RESPONSE SCHEMA NOT SPECIFIED]» | Note appears in detail view |
| AlertDetail | View location (P1) | `AlertDetail.jsx` | `GET /api/geolocation/{ip}` | `routes_geolocation.py` → `geolocation/geolocation_service.py` | `geo_cache` / MaxMind `.mmdb` | Geolocation JSON w/ `is_approximate` | "Approximate Location" renders |
| AlertHistory | Apply filters | `FilterBar.jsx` | `GET /api/alerts/history` | `routes_alerts.py` → `alert_repository.py` | `alerts` table | Filtered alert list | Table re-renders |
| NetworkGraph (P2) | Page load | `NetworkGraph.jsx` | «[API ENDPOINT NOT SPECIFIED IN ARCHITECTURE]» | — | Aggregated flow/alert data | — | Graph renders |

---

## 7. API Interaction Flow

For every API in `architecture.md` §11:

**`GET /api/status`**
- Purpose: system / passive-mode / degraded status (feeds `ZeroOutboundBadge`, FR-018).
- Called from: MainDashboard.
- Triggering action: page load, periodic poll «[ASSUMPTION on poll interval]».
- Request data: none.
- Auth: none (no auth implemented in MVP — §2).
- Backend processing: `routes_status.py` reads pipeline state (`backend/core/degraded_mode.py`).
- Data source: in-memory pipeline state.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: renders live/degraded status.
- Error behavior: «[ASSUMPTION — not specified]».
- Loading behavior: «[ASSUMPTION — not specified]».

**`GET /api/stats/live`**
- Purpose: packets scanned, flows analyzed, threats detected, safe traffic.
- Called from: MainDashboard.
- Triggering action: page load; kept current via `/ws/alerts` push thereafter.
- Request data: none.
- Auth: none.
- Backend processing: aggregation over `flows`/`alerts` tables.
- Data source: SQLite.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: populates counters/charts.
- Error/Loading behavior: «[ASSUMPTION — not specified]».

**`GET /api/alerts`**
- Purpose: live + historical alerts, filterable.
- Called from: MainDashboard (initial feed hydrate, presumably) and/or AlertHistory.
- Request data: filter params «[REQUEST SCHEMA NOT SPECIFIED]».
- Auth: none.
- Backend processing: `routes_alerts.py` → `alert_repository.py`.
- Data source: `alerts` table.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: populates LiveAlertFeed and/or fallback list during WS disconnect (`architecture.md` §24 failure table: "Frontend falls back to short-interval polling of `/api/alerts`").
- Error/Loading behavior: «[ASSUMPTION — not specified]».

**`GET /api/alerts/{id}`**
- Purpose: full alert detail.
- Called from: AlertDetail (on open).
- Request data: `id` path param.
- Auth: none.
- Backend processing: `routes_alerts.py` → `alert_repository.py`, joined with `flows`/`features`/`model_results`.
- Data source: SQLite (`alerts`, `flows`, `features`, `model_results`, linked by `correlation_id`).
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: renders AlertDetail.
- Error behavior: invalid alert ID is a tested error path (`architecture.md` §19); exact response «[RESPONSE SCHEMA NOT SPECIFIED]».
- Loading behavior: «[ASSUMPTION — not specified]».

**`POST /api/alerts/{id}/ack`**
- Purpose: acknowledge an alert.
- Called from: AlertDetail, AlertHistory row action.
- Triggering action: click "Acknowledge."
- Request data: `id` path param; body «[REQUEST SCHEMA NOT SPECIFIED]».
- Auth: none.
- Backend processing: `alert_repository.py` updates `status`.
- Data source: `alerts` table.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: status badge updates.
- Error/Loading behavior: «[ASSUMPTION — not specified]».

**`POST /api/alerts/{id}/false-positive`** — same shape as `/ack`, sets `status = 'false_positive'`.

**`POST /api/alerts/{id}/notes`** — same shape as `/ack`; body presumably contains note text «[REQUEST SCHEMA NOT SPECIFIED]».

**`GET /api/alerts/history`**
- Purpose: filtered history (date, category, severity, source IP, status).
- Called from: AlertHistory.
- Request data: filter query params «[REQUEST SCHEMA NOT SPECIFIED]».
- Auth: none.
- Backend processing: `alert_repository.py` filtered query.
- Data source: `alerts` table.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: table renders.
- Error/Loading/Empty behavior: see Sections 14–15.

**`POST /api/simulator/normal/start` / `/stop`**
- Purpose: control the normal-traffic simulator.
- Called from: SimulatorControls.
- Backend processing: `simulator/normal_traffic_simulator.py` start/stop, independent thread/task pushing into the ingestion queue.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: button state toggles running/stopped.

**`POST /api/simulator/attack/{scenario}/start` / `/stop`**
- Purpose: control a specific attack scenario (port scan, network scan, DDoS-like flood, exfiltration, beaconing, unknown anomaly).
- Called from: SimulatorControls.
- Backend processing: `simulator/attack_simulator.py` + the matching `scenarios/*.py` class.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: scenario marked active; resulting alert appears via WS.

**`POST /api/pcap/upload`**
- Purpose: upload + replay a PCAP.
- Called from: «[ASSUMPTION — no dedicated component named]».
- Backend processing: `routes_pcap.py` → `network/pcap_reader.py` → orchestrator.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: «[ASSUMPTION — not specified]».

**`GET /api/models/status`**
- Purpose: model versions, load state, degraded flag.
- Called from: «[ASSUMPTION — not shown consuming this in any named frontend page/component]».
- Backend processing: `ml/model_registry.py`.
- Response: «[RESPONSE SCHEMA NOT SPECIFIED]».
- Frontend behavior: «[ARCHITECTURE GAP — no frontend consumer identified]».

**`GET /api/geolocation/{ip}`**
- Purpose: approximate geolocation lookup.
- Called from: AlertDetail.
- Backend processing: `routes_geolocation.py` → `geolocation/geolocation_service.py` (private-IP check → cache → MaxMind `.mmdb` or configured provider).
- Response: `{country, state, city, lat, lon, is_approximate: true}` or `{status: "unavailable"}` or `{status: "private/local"}` (`architecture.md` §17 — this is the one endpoint whose response shape *is* specified).
- Frontend behavior: renders as "Approximate Location," never as attacker attribution (`is_approximate` is a mandatory field so this caveat can't be silently dropped).
- Error behavior: unavailable → "Location unavailable" shown; never blocks alert generation (`architecture.md` §24 failure table).

**`WS /ws/alerts`**
- Purpose: real-time alert + stat push.
- Called from: MainDashboard on load (persistent connection).
- Backend processing: `ws_manager.py`, fed by `backend/pipeline/orchestrator.py` after each flow completes scoring.
- Data source: live pipeline output, not a stored query.
- Response: streamed AlertEvent JSON objects.
- Frontend behavior: WS event → store update → component re-render (data-contract tested against `backend/api/schemas.py` per `architecture.md` §19).
- Error behavior: on disconnect, frontend falls back to short-interval polling of `GET /api/alerts` until WS reconnects (`architecture.md` §24).

---

## 8. Data Flow

Per `architecture.md` §6, the canonical object chain for every unit of traffic:

```
RawPacket (network/)
 ↓ Source: live capture interface / simulator / PCAP replay
ValidatedPacket
 ↓ Transformation: packet_validator.py drops packets missing required header fields (FR-006)
DedupedPacket
 ↓ Transformation: deduplicator.py drops repeats/replays
FlowRecord {src_ip, dst_ip, src_port, dst_port, proto, pkt_count, byte_count, timestamps[], ttl_flags(meta only)}
 ↓ Transformation: flow_aggregator.py groups by (src_ip, dst_ip, src_port, dst_port, protocol) over the sliding window
FeatureVector {13 numeric features, source_baseline_ref}
 ↓ Transformation: ml/feature_extraction.py (pure function, no I/O)
NormalizedFeatureVector
 ↓ Transformation: feature_normalizer.py, normalized against learned per-source baseline
{ rf_output: {class, probability}, if_output: {anomaly_score} }
 ↓ Processing: ml/supervised/random_forest_model.py + ml/unsupervised/isolation_forest_model.py
FusedSignal {combined_score_0_1, agreement}
 ↓ Processing: ml/fusion/score_fusion.py
RiskResult {risk_score_0_100, severity, confidence, threat_category}
 ↓ Processing: backend/risk/risk_engine.py + severity_mapper.py + confidence_engine.py
Explanation {text, top_features[]}
 ↓ Processing: backend/risk/explainer.py
AlertRecord {all of the above + flow_id + correlation_id + geolocation}
 ↓ Storage: storage/repositories (flows, features, model_results, alerts tables — linked by correlation_id)
WebSocket AlertEvent (JSON)
 ↓ Delivery: backend/api/ws_manager.py
Frontend store
 ↓ Update: React context + WS event reducer
UI (TrafficChart, ThreatBreakdown, LiveAlertFeed, AlertDetail, AlertHistory)
```

Every object in this chain is a typed dataclass/Pydantic model defined once (`network/flow_models.py`, `backend/api/schemas.py`) and reused across the pipeline — no ad hoc dicts cross module boundaries (`architecture.md` §6).

**Note:** an alert is only generated (and thus only reaches storage/WS/UI) when the combined risk score exceeds the configurable alerting threshold (PRD §12: e.g., >40 for Low/Medium visibility, >80 for Critical prominence). Flows scoring below threshold are still counted in the live stats but do not produce a persisted `alerts` row — the exact threshold value and its config location are «[ASSUMPTION — PRD gives an example value; architecture.md does not name a specific settings key for the alerting threshold itself, only for model weights (`config/risk_weights.yaml`) and the flow window (`config/default.yaml`)]».

---

## 9. Real-Time / Live Data Flow

**What data is live:** flow counters, traffic-volume chart, threat/safe breakdown, and the alert feed (PRD §6.6).

**Where it originates:** `backend/pipeline/orchestrator.py`, after each flow completes the full scoring chain (Section 8).

**How frequently it updates:** Continuously, per completed flow — target end-to-end latency (ingestion to dashboard) is under 2 seconds (PRD FR-020, §17 success metric).

**Mechanism:** WebSocket, native to FastAPI (`architecture.md` §21, §11: `WS /ws/alerts`). `architecture.md` §22 notes this was chosen over SSE/polling (rationale detail itself is referenced but not reproduced in the architecture doc's visible content — «[ARCHITECTURE GAP — §22 rationale reference points to itself, no separate rationale section is present in the provided architecture.md content]»).

**Backend component:** `backend/api/ws_manager.py`, fed by the orchestrator's broadcast step.

**What happens when the connection is lost:** Frontend falls back to short-interval polling of `GET /api/alerts` until the WebSocket reconnects (`architecture.md` §24 failure table).

**How the UI indicates live/stale/offline status:** Not explicitly specified beyond the StatusBar's general system-status indicator — «[ASSUMPTION — no distinct "WS connected / polling fallback" UI indicator is named]».

```
Data Source (live capture / simulator / PCAP)
 ↓
Ingestion Layer (network/ validator, deduplicator, flow_aggregator)
 ↓
Processing (ml/ feature extraction + RF + IF, backend/risk/ fusion + scoring)
 ↓
Real-Time Service (backend/pipeline/orchestrator.py → backend/api/ws_manager.py)
 ↓
WebSocket (/ws/alerts)
 ↓
Frontend Listener (React WS event reducer)
 ↓
State Update (React context)
 ↓
Chart / Feed Update (TrafficChart, ThreatBreakdown, LiveAlertFeed)
```

---

## 10. Authentication and Authorization Flow

`architecture.md` §20/§21 places "authentication on the API" strictly in **P2**, designed as middleware that can be toggled off without touching P0 code paths. **No login, registration, session, or token flow is specified anywhere in either source document for the MVP.** PRD §18 only states a conditional: *"if any authentication is implemented for the dashboard, passwords must be hashed and sessions/tokens handled securely — kept minimal and simple for MVP rather than a full RBAC system."*

```
User
 ↓
(No login step in MVP — direct access to MainDashboard)
 ↓
Application (all users share identical capabilities — see §2)
```

- Login: not designed — «[ARCHITECTURE GAP]».
- Registration: not applicable; no user-account concept appears anywhere in either document.
- Session/token handling: not designed for MVP.
- Role determination: none — no role is derived at runtime (§2).
- Protected routes: none of the routes in the §11/§7 API table are described as requiring auth.
- Unauthorized behavior: not applicable in MVP.
- Logout: not applicable in MVP.
- Session expiration: not applicable in MVP.

This is flagged formally in Section 22.

---

## 11. State Management

| Screen/Feature | Initial | Loading | Success | Empty | Error | Real-time update |
|---|---|---|---|---|---|---|
| MainDashboard — Status | — | fetching `/api/status` | status/badge shown | n/a | «[ASSUMPTION — not specified]» | pushed via WS |
| MainDashboard — Charts/Counters | zeroed | fetching `/api/stats/live` | populated charts | zero-state charts «[ASSUMPTION]» | «[ASSUMPTION — not specified]» | pushed via WS |
| MainDashboard — LiveAlertFeed | empty list | connecting to WS | list of alerts | "no alerts yet" «[ASSUMPTION]» | fallback to polling on WS disconnect (specified) | pushed via WS |
| AlertDetail | — | fetching `/api/alerts/{id}` | full record rendered | n/a (requires a valid ID) | invalid-ID error path exists (tested, per §19), rendering unspecified | n/a (point-in-time view) |
| AlertHistory | default/unfiltered | fetching `/api/alerts/history` | table populated | «[ASSUMPTION — not specified: "no results" message]» | «[ASSUMPTION — not specified]» | not real-time (query-on-demand) |
| SimulatorControls | idle | request in flight «[ASSUMPTION]» | scenario running / stopped | n/a | «[ASSUMPTION — not specified]» | n/a |
| PCAP Upload | idle | uploading/processing «[ASSUMPTION]» | resulting alerts appear via WS | n/a | malformed-PCAP path is tested (§19); user-facing behavior unspecified | n/a |
| Degraded ML mode (system-wide) | n/a | n/a | n/a | n/a | `severity="Unknown - ML Unavailable"`, `risk_score=null`; ingestion/dashboard continue (FR-021, `degraded_mode.py`) | pushed via WS same as normal flows |

```
Initial
 ↓
Loading
 ├── Success → Display Data
 ├── Empty → Empty State «[ASSUMPTION on exact copy/behavior throughout]»
 └── Error → Error State «[ASSUMPTION on exact copy/behavior throughout, except where noted above]»
```

---

## 12. Error and Edge-Case Flows

| Condition | Detection | User Feedback | Recovery |
|---|---|---|---|
| Malformed/incomplete packet headers | `network/packet_validator.py` drops and logs (FR-006) | Not user-facing; packet simply excluded | N/A — by design |
| Duplicate/replayed packets | `network/deduplicator.py` | Not user-facing | N/A — by design |
| ML inference throws/unavailable | `backend/core/degraded_mode.py` catches it, marks pipeline `DEGRADED` (FR-021) | Flow still appears with `severity="Unknown - ML Unavailable"`, `risk_score=null` | Pipeline continues; recovers automatically when ML becomes available again (`architecture.md` §24) |
| Live capture fails / no mirror port | `network/interface_guard.py` / capture layer | «[ASSUMPTION — not specified in UI terms]» | Falls back entirely to `normal_traffic_simulator.py` + `attack_simulator.py` (`architecture.md` §24) — demo scripted with zero live-network dependency |
| WebSocket disconnects | Frontend WS client | «[ASSUMPTION — not specified: banner/indicator]» | Falls back to short-interval polling of `/api/alerts` until WS reconnects (`architecture.md` §24) |
| Invalid/unauthorized alert ID | `routes_alerts.py` | «[RESPONSE SCHEMA NOT SPECIFIED]» | Tested error path (`architecture.md` §19); exact UI response unspecified |
| Malformed PCAP upload | `routes_pcap.py` / `pcap_reader.py` | «[RESPONSE SCHEMA NOT SPECIFIED]» | Tested error path (`architecture.md` §19); exact UI response unspecified |
| Geolocation DB/provider unavailable | `geolocation_service.py` | "Location unavailable" shown | Never blocks alert generation (`architecture.md` §24) |
| SQLite write contention/corruption risk under load | Single-writer pattern + WAL mode | Not user-facing (mitigated architecturally) | WAL mode prevents most contention (`architecture.md` §24) |
| Detection-relevant errors generally (malformed input, inference failure) | Structured, timestamped logging (FR-022) | Not necessarily user-facing | Logged for post-hoc review |
| Timeout on any API call | Not specified | «[ASSUMPTION — not specified]» | «[ASSUMPTION — not specified]» |
| Duplicate user action (e.g., double-click Acknowledge) | Not specified | «[ASSUMPTION — not specified]» | «[ASSUMPTION — not specified]» |
| Stale data after reconnect | Not specified beyond the WS→polling fallback itself | «[ASSUMPTION — not specified]» | «[ASSUMPTION — not specified]» |
| Empty datasets (e.g., no alerts in a filtered range) | Query returns zero rows | «[ASSUMPTION — not specified]» | User adjusts filters |

**Note:** the sub-2-second latency, degraded-mode behavior, and WS→polling fallback are the only failure/edge behaviors given explicit, specific treatment in the source documents. All other rows above are marked as assumptions or gaps rather than invented behavior, per the task's Rule 7 (cover failure paths) balanced against Rule 2/3 (don't invent APIs/schemas).

---

## 13. Loading, Empty, and Error States

For MainDashboard, AlertDetail, and AlertHistory — the three P0/P1 screens with defined data dependencies:

**MainDashboard**
- Loading: «[ASSUMPTION — not specified: spinner/skeleton]» while `/api/status` and `/api/stats/live` resolve and the WS connection establishes.
- Empty: «[ASSUMPTION — not specified]» state if no flows have been ingested yet (e.g., before the simulator or live capture starts).
- Error: «[ASSUMPTION — not specified]» if `/api/status` or `/api/stats/live` fail; WS-specific error handling (disconnect → polling fallback) *is* specified (§9, §12).
- Retry: not specified beyond the automatic WS→polling fallback, which is itself a form of automatic recovery rather than a user-triggered retry.

**AlertDetail**
- Loading: «[ASSUMPTION — not specified]» while `/api/alerts/{id}` resolves.
- Empty: not applicable — screen requires a valid alert ID to render at all.
- Error: invalid alert ID is a tested backend path; the resulting UI treatment is «[ASSUMPTION — not specified]».
- Retry: «[ASSUMPTION — not specified]».

**AlertHistory**
- Loading: «[ASSUMPTION — not specified]» while `/api/alerts/history` resolves.
- Empty: «[ASSUMPTION — not specified]» if the filter set matches zero alerts.
- Error: «[ASSUMPTION — not specified]».
- Retry: «[ASSUMPTION — not specified]».

This is a genuine gap: neither document specifies loading/empty/error copy or components for any screen. It is flagged in Section 22 as a `[PRD GAP]` / `[ARCHITECTURE GAP]` pair.

---

## 14. Notifications and Feedback

The source documents specify very little about toasts, dialogs, or explicit confirmation UI. What **is** specified:

- **ZeroOutboundBadge / StatusBar:** a persistent status indicator confirming passive-only operation (FR-018) — this is the one always-visible, standing "notification."
- **Severity color-coding on alerts:** LiveAlertFeed and AlertHistory both color-code by severity (PRD §11, §12) — a persistent visual signal rather than a transient toast.
- **Alert deduplication:** repeated qualifying flows from the same source within 60 seconds are aggregated into one alert with an updated last-seen time and incrementing event count (PRD §12, FR-017) — this is itself a form of feedback (an existing alert "grows" rather than spamming new ones).

Everything else — success toasts for Acknowledge/False Positive/Notes, upload-progress indicators, confirmation dialogs before destructive-feeling actions, WS-disconnect banners — is **not specified** in either source document. Per Rule 2/3/4 of the generating task, these are left unspecified rather than invented; see Section 22.

---

## 15. External Services and Integrations

| External Service | Purpose | Trigger | Data Sent | Data Received | Failure Handling |
|---|---|---|---|---|---|
| MaxMind GeoLite2 (local `.mmdb`) — or a configured external geolocation provider if explicitly enabled | Approximate IP geolocation for AlertDetail (P1) | `GET /api/geolocation/{ip}` call, itself triggered by opening AlertDetail | Source IP | `{country, state, city, lat, lon, is_approximate: true}`, or `{status: "unavailable"}` / `{status: "private/local"}` | "Location unavailable" shown; never blocks alert generation (`architecture.md` §24) |

No other external service or integration is named in either document. Both explicitly rule out live internet dependency for the core demo (PRD §19, §26; `architecture.md` §24) — the entire pipeline runs locally, and the geolocation lookup itself defaults to an offline `.mmdb` file rather than a live external call. Downstream SOAR/ticketing integration is explicitly listed only as a **Future Enhancement**, beyond MVP scope (PRD §27; `architecture.md` §20 does not include it even at P2).

---

## 16. AI/ML Flow

```
FlowRecord (network/)
 ↓
Preprocessing: feature_normalizer.py — normalize raw counts against learned per-source baseline
 ↓
AI/ML Model:
   ├── Random Forest (ml/supervised/random_forest_model.py) — supervised classifier
   └── Isolation Forest (ml/unsupervised/isolation_forest_model.py) — unsupervised anomaly detector
 ↓
Inference:
   RF → {class, probability}
   IF → {anomaly_score}
 ↓
Post-processing: ml/fusion/score_fusion.py combines both signals per the fusion policy
 ↓
Backend: backend/risk/risk_engine.py (0–100 score) → severity_mapper.py (band) →
         confidence_engine.py (confidence from model agreement + data sufficiency) →
         explainer.py (feature-based plain-language explanation)
 ↓
Frontend: AlertEvent pushed via /ws/alerts → LiveAlertFeed / AlertDetail
 ↓
User: reviews score, category, confidence, and explanation
```

**Model purpose:**
- Random Forest — recognize known attack shapes (Port Scan, Network Scan, DDoS/Flood, Exfiltration, Beaconing where evidence supports it), multi-class over `{Benign, ...}` (`architecture.md` §7), trained on CICIDS2017/CSE-CIC-IDS2018 (or NSL-KDD/UNSW-NB15) after forward-flow filtering (PRD §16).
- Isolation Forest — establish a benign baseline and flag statistical outliers, catching covert-channel/zero-day behavior the supervised model was never trained on (PRD §7, §3).

**Input:** the 13-feature `FeatureVector` (packet count, byte count, mean IAT, IAT variance, unique dest IP/port counts, protocol distribution, packet-size ratios, entropy — `architecture.md` §5, §6).

**Processing:** both models run per flow; `score_fusion.py` combines them.

**Fusion / classification policy** (`architecture.md` §7): if RF probability for a known class exceeds a configurable confidence threshold → classify as that known threat; else if IF anomaly score exceeds its threshold → "Unknown Anomaly"; else → benign. Both scores still jointly feed the 0–100 risk score (weighted sum, weights in `config/risk_weights.yaml`).

**Output:** combined 0–100 risk score, severity band, confidence value, threat category (or "Unknown Anomaly"), and a 2–3 line explanation naming top contributing features.

**Where inference occurs:** in-process, within the same Python backend (`ml/inference_service.py`), not a separate service — this is a modular monolith (`architecture.md` §1).

**How results reach the UI:** via the standard pipeline → storage → WebSocket path described in Sections 8–9.

**Loading/progress state:** not applicable per-inference (sub-2-second, synchronous within the pipeline call chain); `GET /api/models/status` exposes model load state/degraded flag at a system level, though no frontend consumer for that specific endpoint is named (§7, §22).

**Failure behavior:** if ML inference throws, `backend/core/degraded_mode.py` catches it and the flow is still passed through with `risk_score=null, severity="Unknown - ML Unavailable"` rather than crashing ingestion or the dashboard (FR-021).

**No deep learning** is used — explicitly ruled out as unjustified for tabular flow metadata at this scale in favor of RF + IF (`architecture.md` §7).

---

## 17. Complete System Flow

```
USER (SOC Analyst / Network Admin / Security Lead / Presenter)
 ↓
FRONTEND (React SPA: MainDashboard, AlertDetail, AlertHistory, NetworkGraph[P2])
 ↓
API (FastAPI REST — backend/api/routes_*.py — and WebSocket — ws_manager.py)
 ↓
BACKEND (backend/pipeline/orchestrator.py wiring every stage below)
 ↓
BUSINESS LOGIC
   Ingestion (network/ or simulator/ or PCAP)
     → Validation/Dedup/Aggregation
     → Feature Extraction (ml/feature_extraction.py, feature_normalizer.py)
     → Hybrid ML (Random Forest + Isolation Forest, ml/fusion/score_fusion.py)
     → Risk Engine + Severity + Confidence + Explanation (backend/risk/*)
 ↓
DATABASE / AI / EXTERNAL SERVICES
   SQLite (storage/, tables: flows, features, model_results, alerts)
   Trained model artifacts (models/trained/*.pkl via ml/model_registry.py)
   Geolocation (MaxMind GeoLite2 / configured provider)
 ↓
RESPONSE
   REST responses (status, stats, alert queries, action confirmations)
   WebSocket AlertEvent stream
 ↓
FRONTEND STATE (React context + WS event reducer)
 ↓
UI (StatusBar/ZeroOutboundBadge, TrafficChart, ThreatBreakdown, LiveAlertFeed,
    AlertDetail, AlertHistory, NetworkGraph[P2])
```

This diagram makes explicit that `prd.md`'s functional requirements (Section 13) are realized entirely through the modular-monolith pipeline described in `architecture.md` §1–§9, with the **one-directional queue** between `network/`/`simulator/` and `backend/pipeline/orchestrator.py` acting as the software-simulated diode (`architecture.md` §18) — the architectural mechanism that structurally enforces PRD's "zero return traffic" non-goal-turned-hard-requirement (FR-001, FR-019).

---

## 18. Screen-to-Requirement Traceability

| PRD Requirement | Feature | Screen | User Action | Backend/API | Architecture Component |
|---|---|---|---|---|---|
| FR-001, FR-019 | One-way ingestion (6.1) | MainDashboard (StatusBar) | passive viewing | `GET /api/status` | `network/passive_capture.py`, `interface_guard.py` |
| FR-002 | Simulator (6.1) | MainDashboard (SimulatorControls) | start baseline / trigger scenario | `POST /api/simulator/normal/start`, `POST /api/simulator/attack/{scenario}/start` | `simulator/normal_traffic_simulator.py`, `attack_simulator.py`, `scenarios/*.py` |
| FR-003 | PCAP upload (6.8) | MainDashboard («[ASSUMPTION]» component) | upload file | `POST /api/pcap/upload` | `network/pcap_reader.py` |
| FR-004 | Flow grouping | (not directly user-facing) | — | — | `network/flow_aggregator.py`, `flow_models.py` |
| FR-005 | Feature extraction (6.2) | AlertDetail (evidence display) | view alert | `GET /api/alerts/{id}` | `ml/feature_extraction.py` |
| FR-006 | Drop malformed packets | (not user-facing) | — | — | `network/packet_validator.py` |
| FR-007, FR-008 | Hybrid detection + risk score (6.3, 6.4) | AlertDetail | view alert | `GET /api/alerts/{id}` | `ml/supervised/`, `ml/unsupervised/`, `ml/fusion/score_fusion.py`, `backend/risk/risk_engine.py` |
| FR-009 | Severity banding (6.4) | LiveAlertFeed, AlertDetail, AlertHistory | view alert(s) | `GET /api/alerts`, `GET /api/alerts/{id}` | `backend/risk/severity_mapper.py` |
| FR-010, FR-011 | Category / Unknown Anomaly labeling (6.9) | AlertDetail | view alert | `GET /api/alerts/{id}` | fusion policy (`ml/fusion/score_fusion.py`, `architecture.md` §7) |
| FR-012 | Explanation (6.5) | AlertDetail | view alert | `GET /api/alerts/{id}` | `backend/risk/explainer.py` |
| FR-013 | Alert persistence (6.7) | AlertHistory | — | (write path, not user-triggered) | `storage/repositories/alert_repository.py` |
| FR-014 | Live dashboard (6.6) | MainDashboard | passive viewing | `GET /api/status`, `GET /api/stats/live`, `WS /ws/alerts` | `backend/api/ws_manager.py`, all `frontend/src/components/` |
| FR-015 | Alert history + filtering (6.7) | AlertHistory | apply filters | `GET /api/alerts/history` | `FilterBar.jsx`, `alert_repository.py` |
| FR-016 | Acknowledge / False Positive | AlertDetail, AlertHistory | click action | `POST /api/alerts/{id}/ack`, `POST /api/alerts/{id}/false-positive` | `alert_repository.py` |
| FR-017 | 60s dedup/aggregation | LiveAlertFeed | passive viewing | `WS /ws/alerts` | `backend/pipeline/orchestrator.py` (dedup logic — exact module not individually named beyond the orchestrator) |
| FR-018 | Zero-outbound indicator | MainDashboard (StatusBar) | passive viewing | `GET /api/status` | `ZeroOutboundBadge.jsx`, `scripts/verify_zero_outbound.py` |
| FR-020 | Sub-2s latency | (system-wide, cross-cutting) | — | — | full pipeline, `backend/pipeline/orchestrator.py` |
| FR-021 | Degraded mode | MainDashboard, AlertDetail | passive viewing | — | `backend/core/degraded_mode.py` |
| FR-022 | Structured error logging | (not user-facing) | — | — | `backend/core/logging_setup.py`, `errors.py` |
| 6.10 (Network Relationship View, P2) | — | NetworkGraph | passive viewing | «[API ENDPOINT NOT SPECIFIED IN ARCHITECTURE]» | `NetworkGraph.jsx` |
| 6.11 (Demo Control Panel) | — | MainDashboard (SimulatorControls) | start/stop demo elements | simulator routes (above) | `simulator/demo_controller.py` (P1) |

**Orphaned requirement:** none of FR-001–FR-022 lack a corresponding screen/workflow/component above, satisfying the internal-consistency check required by the generating task's Rule 10.

---

## 19. Architecture-to-UI Traceability

| Architecture Component | Purpose | Used By | Screen/Feature | Data Flow |
|---|---|---|---|---|
| `network/` (passive_capture, pcap_reader, packet_validator, deduplicator, flow_aggregator, interface_guard) | Ingestion, validation, flow grouping | `backend/pipeline/orchestrator.py` | Indirectly all screens (source of every flow) | RawPacket → FlowRecord (§8) |
| `ml/` (feature_extraction, supervised, unsupervised, fusion, model_registry, inference_service) | Feature extraction + hybrid scoring | orchestrator | AlertDetail (score, category, confidence) | FlowRecord → RiskResult (§8, §16) |
| `backend/risk/` (risk_engine, severity_mapper, confidence_engine, explainer) | Score → severity → confidence → explanation | orchestrator | LiveAlertFeed, AlertDetail, AlertHistory | RiskResult → Explanation → AlertRecord |
| `backend/pipeline/orchestrator.py` | End-to-end wiring | — | All screens (indirectly) | Full chain, §8 |
| `backend/core/` (logging, errors, degraded_mode) | Cross-cutting reliability | orchestrator, all backend modules | MainDashboard (degraded status) | FR-021, FR-022 |
| `storage/` (SQLite, repositories) | Persistence | `backend/api`, `backend/pipeline` | AlertHistory, AlertDetail | AlertRecord → SQLite rows |
| `backend/api/` (routes_*, ws_manager, schemas) | REST/WS surface | `frontend/` | All screens | See §7 |
| `simulator/` (normal_traffic_simulator, attack_simulator, scenarios, demo_controller) | Demo/testing data source | orchestrator (alternate ingestion source) | MainDashboard (SimulatorControls) | Synthetic FlowRecord → same pipeline |
| `geolocation/` (geolocation_service, geo_cache) | Approximate IP location | `backend/risk/explainer` «[per architecture.md §5]», `backend/api/routes_geolocation` | AlertDetail | IP → geolocation JSON |
| `config/` (settings, default.yaml, risk_weights.yaml) | Centralized configuration | every module | Not user-facing | — |
| `frontend/` (pages, components) | Presentation | — | All screens | See §4, §6 |
| `datasets/` (raw, cleaned, processed, feature_engineered, pipeline adapters) | Offline dataset preprocessing for training | `ml/*/train_*.py` (training-time only) | **None** — not part of the runtime application flow | Not part of the live user-facing flow |
| `models/` (trained/, evaluation/, metadata/) | Trained model artifacts, evaluation metrics | `ml/model_registry.py` | AlertDetail (indirectly, via inference) | Model files → inference → RiskResult |
| `scripts/verify_zero_outbound.py` | Static + runtime zero-outbound verification | CI, live demo step | MainDashboard (`ZeroOutboundBadge`, indirectly — the badge reflects the guarantee this script verifies, but does not call it live) | Not a runtime API call |

**Orphaned/under-represented components identified by this matrix:**
- `datasets/` — training-time only, correctly has no runtime UI representation; not an error, but worth naming explicitly per the traceability requirement.
- `geolocation/` — has full architectural treatment (§17 of `architecture.md`) and a live UI consumer (AlertDetail) and an API route, but **no corresponding PRD feature or FR** names geolocation anywhere in `prd.md`. This is flagged as a `[CONFLICT]`/`[ARCHITECTURE GAP]` in Section 22.
- `NetworkGraph.jsx` — has a named PRD feature (6.10) but no named backing API endpoint in `architecture.md` §11. Flagged in Section 22.
- `GET /api/models/status` — has no named frontend consumer in `architecture.md`'s component list. Flagged in Section 22.

---

## 20. Open Questions, Gaps, and Conflicts

**«[CONFLICT]» Alert lifecycle vs. database schema.**
What: PRD §12 defines the alert lifecycle as `New → Acknowledged → (Investigating) → Resolved / False Positive`. `architecture.md` §10's SQLite schema constrains `alerts.status` to `CHECK(status IN ('new','acknowledged','false_positive'))` — there is no `investigating` or `resolved` state in the database.
Why it matters: if the PRD's lifecycle is taken literally, two of its four/five states are unpersistable in the current schema.
Decision required: either the PRD's lifecycle description is aspirational/simplified for MVP (and the actual MVP lifecycle is just `new → acknowledged → false_positive`, matching Section 12/16 above, which describe only Acknowledge and False Positive as implemented actions), or the schema needs an `investigating`/`resolved` extension. This document has conservatively followed the schema (three states) for all MVP-facing flows above, per the task's "resolve ambiguity conservatively" rule, but flags the mismatch rather than silently resolving it.

**«[ARCHITECTURE GAP]» Geolocation has no PRD-side feature or requirement.**
What: `architecture.md` gives geolocation a full architecture section (§17), a database field (`alerts.geolocation`), an API route (`GET /api/geolocation/{ip}`), and a named frontend consumer (AlertDetail's "Approximate Location"). No section of `prd.md` — not the Core Features (§6), not the Functional Requirements (§13), not the Data Requirements (§15) — mentions geolocation.
Why it matters: it's a fully-specified architecture component with no traceable product requirement backing it (the inverse of an orphaned requirement — an orphaned architecture component).
Decision required: confirm geolocation is an intentional architecture-team addition consistent with the product vision (plausible, given AlertDetail's "full flow metadata" framing in PRD §11) versus scope creep beyond what was actually requested.

**«[ARCHITECTURE GAP]» No frontend component named for PCAP upload.**
What: `POST /api/pcap/upload` exists (`architecture.md` §11, `routes_pcap.py`) and the feature is specified in PRD §6.8/FR-003, but no page or component in `architecture.md`'s `frontend/src/` tree (§3) is dedicated to it.
Why it matters: a developer building the frontend has an endpoint but no specified UI location or interaction pattern for it.
Decision required: confirm whether PCAP upload belongs inside `SimulatorControls.jsx`, a new modal, or a new dedicated component.

**«[ARCHITECTURE GAP]» `NetworkGraph.jsx` has no backing API endpoint.**
What: PRD §6.10 and `architecture.md` §3/§12 both specify a Network Relationship View, but the API table (`architecture.md` §11) contains no endpoint for aggregated flow/relationship data.
Why it matters: this P2 screen cannot be implemented against the currently-specified API surface.
Decision required: define the missing endpoint (e.g., `GET /api/graph` or similar) when P2 work begins.

**«[ARCHITECTURE GAP]» No frontend consumer named for `GET /api/models/status`.**
What: the endpoint is specified, but no page/component in `architecture.md`'s frontend tree is described as calling it.
Why it matters: model version/degraded-state visibility (a reasonable trust signal, parallel to `ZeroOutboundBadge`) may go unsurfaced to the user.
Decision required: confirm whether this belongs on the StatusBar or is intentionally backend/ops-only for MVP.

**«[ARCHITECTURE GAP]» No retrain-trigger endpoint despite a named P2 feature.**
What: PRD §6 (Feature Priority Matrix, §24) and `architecture.md` §20 both list a manual "simulate retraining" control as P2, but the API table has no `POST /api/models/retrain` (or equivalent) route.
Why it matters: the P2 feature cannot be implemented against the currently-specified API surface.
Decision required: define the missing endpoint when P2 work begins.

**«[PRD GAP]» / «[ARCHITECTURE GAP]» No request/response schemas specified for most endpoints.**
What: only `GET /api/geolocation/{ip}`'s response shape is explicitly given (`architecture.md` §17). Every other endpoint in §11 has no documented request or response body.
Why it matters: a developer or coding agent cannot implement the frontend/backend contract without inventing schemas, which the generating task explicitly forbids.
Decision required: produce (or point to) `backend/api/schemas.py` content, referenced but not reproduced in `architecture.md`.

**«[PRD GAP]» / «[ARCHITECTURE GAP]» No loading/empty/error state designs.**
What: neither document specifies loading indicators, empty-state copy/visuals, or error-state UI for any screen, beyond the WS-disconnect→polling fallback and the ML-degraded-mode severity label.
Why it matters: Section 13's near-total reliance on «[ASSUMPTION — not specified]» markers means a developer has no source-of-truth UI/UX spec for these common states.
Decision required: a UX pass is needed before implementation to define these states.

**«[ASSUMPTION]» Alerting threshold value and config location.**
What: PRD §12 gives example threshold values (>40 visibility, >80 Critical prominence) but `architecture.md` never names a specific settings key for the alert-generation threshold itself (only `config/risk_weights.yaml` for model-output weighting and `config/default.yaml` for the flow window are named).
Why it matters: the exact trigger condition for "does this flow become a persisted alert" is not pinned down precisely enough to implement without an assumption.
Decision required: confirm the threshold lives in `config/default.yaml` (most likely, by elimination) and its exact default value.

**«[ASSUMPTION]» No RBAC / role differentiation in MVP.**
What: PRD §4 describes four distinct user types with different needs; neither document defines any technical access differentiation between them for MVP (auth itself is P2).
Why it matters: the Section 2 role table in this document is functional/descriptive, not a technical access-control spec — a developer should not build role gating into the MVP based on PRD §4 alone.
Decision required: none required for MVP (this is explicitly deferred, consistent with both documents); flagged here only so the distinction is not lost.

**«[ASSUMPTION]» Top-level navigation mechanism between pages.**
What: `architecture.md` names four page components (`MainDashboard.jsx`, `AlertDetail.jsx`, `AlertHistory.jsx`, `NetworkGraph.jsx`) but no navigation bar, router config, or menu component.
Why it matters: how a user gets from MainDashboard to AlertHistory or NetworkGraph (other than via an alert-detail deep link) is unspecified.
Decision required: confirm whether `App.jsx` implements a simple router/nav or whether these are intended as tabs/sections within a single page.
