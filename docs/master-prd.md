# Master PRD — OneWay Sentinel
## AI-Based Detection of Cyber Threats in Unidirectional IP Traffic

**Problem Statement:** SIH26145 · **Organization:** National Technical Research Organisation (NTRO)
**Document Status:** Consolidated Master v1.0 · **Context:** Smart India Hackathon

---

## 1. Product Overview

**Product Name:** OneWay Sentinel

**One-line description:** A passive, AI-powered monitoring system that detects cyber threats — including known attack patterns and novel covert-channel exfiltration — in traffic flowing across a unidirectional (data-diode-protected) network link, without ever sending a response through the link.

**Problem statement:** High-security environments (power grids, defense networks, nuclear/ICS-SCADA systems) use data diodes to physically enforce one-way data flow, so that nothing can be sent back into the protected network. This defeats conventional two-way security tools (firewalls, stateful IDS) that depend on handshakes and response traffic to function — and it creates a blind spot: malware or an insider can still smuggle data *out* by encoding it into the timing, size, or pattern of otherwise legitimate outbound traffic (a covert channel). There is currently no reliable way to catch this using tools that require bidirectional state.

**Proposed solution:** A passive traffic inspector that sits on the receiving/monitoring side of the diode, extracts statistical metadata from unidirectional flows (never payload, never a response), and scores every flow using a hybrid machine-learning pipeline — a supervised model for known attack signatures and an unsupervised anomaly model for unknown/covert-channel behavior — surfacing results on a real-time, explainable dashboard.

**Target users:** SOC/duty analysts, network administrators, security team leads, and organizations operating diode-protected infrastructure.

**Primary objective:** Demonstrate, within hackathon constraints, that meaningful real-time threat detection is possible using only one-way flow metadata — with zero bytes ever sent back through the monitored link.

---

## 2. Problem Definition

**Existing problem:** Security teams monitoring diode-protected links have no visibility beyond "traffic is flowing." Standard IDS/firewall logic assumes a two-way conversation (SYN/SYN-ACK/ACK, request/response) to establish state, verify a connection, and detect anomalies like resets or retransmits. None of that exists on a unidirectional link.

**Why unidirectional IP traffic is challenging:**
- No handshake or state to inspect — stateful inspection fails by design.
- No way to confirm whether a connection "succeeded," so response-dependent signals (e.g., failed-login counts) are unavailable.
- Increasing use of encryption makes payload inspection unreliable even where it would otherwise be possible — detection must work on metadata alone.
- An attacker who already knows the link is one-way can shape traffic (e.g., beaconing at fixed intervals, low-and-slow exfiltration) specifically to blend in.

**Current limitations:** Existing commercial tools either don't operate on diode links at all, or fall back to simple volumetric thresholds that miss subtle covert channels and generate high false-positive rates on legitimate bursty traffic.

**Why AI/ML is useful:** Statistical/behavioral patterns (inter-arrival timing, destination diversity, byte-count distributions) that are invisible to rule-based thresholds are exactly what ML models — particularly anomaly detection — are suited to learn and generalize from, including for threats not seen during training.

**Impact of the problem:** Undetected exfiltration or reconnaissance across a diode-protected link can compromise the confidentiality of exactly the systems the diode was installed to protect — critical infrastructure, defense, and industrial control environments.

---

## 3. Goals & Objectives

### Primary Goals
- Detect anomalous and known-malicious patterns in unidirectional outbound traffic in near real time, using passive observation only.
- Operate with **zero return traffic** — no acknowledgement, probe, or response is ever sent back through the monitored link.
- Produce a graded 0–100 risk/suspicion score per flow, with severity bands, instead of a binary flag.
- Provide a human-readable explanation for every alert above the alerting threshold.
- Demonstrate feasibility via a working, runnable prototype using public datasets and/or simulated traffic.

### Secondary Goals
- Classify detected threats into named categories (e.g., port scan, DDoS-like flood, exfiltration, beaconing) where the evidence supports it.
- Provide historical alert review and basic trend visibility for a security lead.
- Keep the system lightweight enough to run on a single laptop for a live demonstration.

### Non-Goals
- **Deep packet inspection** of payloads (privacy, encryption, and speed reasons — metadata only).
- **Active response** of any kind — no TCP resets, no firewall rule changes, no blocking. The system is detect-and-alert only.
- **Brute-force login detection** — without visibility into response/failure codes on a one-way link, distinguishing "failed login attempts" from any other periodic low-volume flow is not reliably possible; this is explicitly out of scope rather than falsely promised.
- Building physical data-diode hardware — the diode is simulated in software (e.g., a one-way queue/socket that never reads incoming data) for the prototype.
- A mobile application — a responsive web dashboard is sufficient.
- Guaranteeing detection of 100% of threats or zero false positives — no detection system can claim this responsibly.

---

## 4. Target Users & Stakeholders

| User | Need |
|---|---|
| **SOC / Duty Analyst** | Real-time visibility into link health, prioritized alerts with clear reasoning, low alert fatigue. |
| **Network Administrator** | Confirmation that unusual activity is a genuine threat and not a misconfiguration; traffic health overview. |
| **Security Team Lead / Manager** | Aggregate view of threat trends over time, audit trail of past alerts and analyst actions. |
| **Deploying Organization (e.g., critical-infrastructure operator)** | A tool that strengthens the diode's protection without ever weakening its one-way guarantee. |

---

## 5. Product Vision

OneWay Sentinel should become the standard "eyes" on the output side of a data diode — the layer that gives security teams the same situational awareness they'd expect from a two-way network, without requiring a single byte to travel backward through the protected boundary. Long term, the vision is a lightweight, explainable, continuously-adapting detection layer deployable anywhere unidirectional flow monitoring is required — not just data diodes, but asymmetric routing, SPAN-mirrored links, and high-speed UDP broadcast environments.

---

## 6. Core Features

### 6.1 One-Way Traffic Ingestion & Simulator — **P0**
- **Purpose:** Capture unidirectional traffic without ever transmitting on the monitored interface.
- **User value:** Analysts see live traffic without risking the diode's integrity; judges/demo users can safely trigger realistic attack scenarios without touching real infrastructure.
- **Functional behavior:** A passive listener captures packets/flows as they arrive on the monitoring interface (no socket-level response capability implemented on that path). A companion synthetic traffic simulator can generate "normal" baseline traffic and inject named attack patterns (port scan, flood, exfiltration, beaconing) on demand for demonstration and testing.
- **Inputs:** Live network interface traffic, or simulator-generated JSON flow events, or an uploaded PCAP (see 6.8).
- **Outputs:** Raw packet/flow records queued for feature extraction.

### 6.2 Feature Extraction Engine — **P0**
- **Purpose:** Convert raw packets into the statistical features the ML models need, without touching payload content.
- **User value:** Enables detection despite encryption and the missing return path.
- **Functional behavior:** Aggregates packets into flows (grouped by source/destination pair over a sliding time window) and computes volume, timing, and diversity metrics (Section 7).
- **Inputs:** Raw packet stream.
- **Outputs:** Feature vectors per flow, stored with a reference back to the source flow for traceability.

### 6.3 Hybrid AI Detection Engine — **P0**
- **Purpose:** Classify known attack patterns and flag unknown anomalies.
- **User value:** Catches both textbook attacks and novel covert-channel behavior an attacker specifically designed to evade signatures.
- **Functional behavior:** Feature vectors are scored by (a) a supervised classifier trained on labeled attack/benign data, and (b) an unsupervised anomaly detector trained only on benign traffic. Scores are combined into a single risk score.
- **Inputs:** Feature vectors.
- **Outputs:** Combined 0–100 risk score, model confidence, and (if applicable) a predicted threat category.

### 6.4 Risk Scoring & Severity Banding — **P0**
- **Purpose:** Give analysts a graded signal instead of a binary alarm, reducing alert fatigue.
- **Functional behavior:** Maps the combined model output to a 0–100 score and a severity band (Informational/Low/Medium/High/Critical).
- **Inputs:** Model outputs.
- **Outputs:** Score + severity label attached to the flow record.

### 6.5 Alert Explanation (Explainable Output) — **P0**
- **Purpose:** Let an analyst understand *why* a flow was flagged, without needing to trust a black box.
- **Functional behavior:** For every alert above the threshold, the system generates a short, human-readable explanation naming the top contributing features (e.g., "destination port diversity is 9x the learned baseline; inter-arrival time is unusually uniform").
- **Inputs:** Feature vector + model's feature-importance/contribution output.
- **Outputs:** 2–3 line plain-language explanation attached to the alert.

### 6.6 Live Security Dashboard — **P0**
- **Purpose:** Give the analyst a single real-time view of link health and active threats.
- **Functional behavior:** Displays system/listening status, packet/flow counters, a live traffic-volume chart, a threat-vs-safe breakdown, and an alert feed — all updating live as flows are scored.
- **Inputs:** Streaming scored flow/alert data.
- **Outputs:** Rendered web dashboard.

### 6.7 Alert Log & History — **P0**
- **Purpose:** Give analysts and leads a durable record for review and reporting.
- **Functional behavior:** Every alert is persisted with timestamp, source IP, category, score, and explanation; searchable/filterable by time range, category, or IP.
- **Inputs:** Generated alerts.
- **Outputs:** Queryable alert history table.

### 6.8 PCAP Upload for Offline Analysis — **P1**
- **Purpose:** Let a user analyze a pre-recorded capture without live traffic, useful for testing and for judges who want to bring their own sample.
- **Functional behavior:** Accepts an uploaded `.pcap` file, runs it through the same feature-extraction and scoring pipeline as live traffic.
- **Inputs:** Uploaded PCAP file.
- **Outputs:** Same scored-flow/alert output as the live path.

### 6.9 Threat Category Classification — **P1**
- **Purpose:** Give alerts a named category, not just a score, to speed analyst triage.
- **Functional behavior:** When the supervised model's confidence is high, the flow is labeled with a specific category (Section 9); otherwise it is labeled "Unknown Anomaly."
- **Inputs:** Model output.
- **Outputs:** Category label on the alert.

### 6.10 Network Relationship View — **P2**
- **Purpose:** Give an at-a-glance view of which source IPs are talking to which destinations and at what risk level.
- **Functional behavior:** A simple node/edge visualization where node color reflects risk and edge thickness reflects traffic volume.
- **Inputs:** Aggregated flow/alert data.
- **Outputs:** Interactive graph view.

### 6.11 Demo / Simulation Control Panel — **P1**
- **Purpose:** Give a presenter a safe, reliable way to trigger each threat scenario live during judging.
- **Functional behavior:** A simple control panel (buttons) to start baseline traffic and inject a chosen attack pattern via the simulator (6.1).
- **Inputs:** Presenter selection.
- **Outputs:** Simulated flow events fed into the ingestion pipeline.

---

## 7. AI/ML System

**Data ingestion:** Flows are assembled from raw packets grouped by (source IP, destination IP) over a fixed sliding window (e.g., 5 seconds), consistent with a source producing a continuous one-way stream.

**Preprocessing:** Packets missing required header fields are dropped and logged; duplicate/replayed packets are deduplicated. No payload bytes are retained at any stage.

**Feature extraction (per flow, per window):**
- *Volume:* total packets, total bytes, average packet size.
- *Timing:* flow duration, mean inter-arrival time (IAT), IAT variance.
- *Diversity:* number of unique destination IPs contacted, number of unique destination ports contacted.
- *Protocol/behavioral:* protocol distribution, ratio of small vs. large packets, byte-size entropy.

**Feature engineering:** Raw counts are normalized against a learned per-source baseline (e.g., "destination port diversity relative to this source's typical behavior") so the model reflects deviation, not just raw magnitude.

**Model pipeline (hybrid):**
- *Supervised component:* A classifier (Random Forest as the MVP baseline; extensible to gradient-boosted trees) trained on labeled flow data to recognize known attack shapes (Section 9). Chosen for training speed, native feature-importance output (supports explainability without extra tooling), and reliability on tabular data — realistic for a hackathon timeline.
- *Unsupervised component:* An anomaly detector (Isolation Forest) trained only on benign traffic to establish a "normal" baseline and flag statistical outliers — this is what catches covert-channel behavior a supervised model was never trained to recognize.
- *Why hybrid:* The supervised model alone would miss novel/zero-day covert channels (the core risk the official problem statement calls out); the anomaly model alone tends to produce more false positives. Combining both, and requiring corroboration for the highest severity bands, balances detection power against alert noise.

**Risk scoring:** The two model outputs are combined into a single 0–100 score (e.g., a weighted combination of supervised attack probability and normalized anomaly deviation), then mapped to a severity band.

**Confidence scoring:** The supervised model's class probability is surfaced alongside the category label; the anomaly model's deviation magnitude is surfaced for "Unknown Anomaly" alerts.

**Explainability:** For tree-based models, per-flow feature contributions (e.g., feature importances / per-prediction contribution) are translated into the plain-language explanation described in 6.5. A richer explanation library (e.g., SHAP-style attribution) is a valid post-MVP upgrade for more precise, per-alert attribution.

**Model evaluation:** Offline evaluation via train/test split and confusion matrix; precision, recall, and F1-score are the primary metrics; false-positive rate on held-out benign traffic is tracked separately.

**Retraining/update strategy:** Models are trained offline before the demo (no online/live learning in MVP). A "retrain" action is out of scope for MVP; a manual, presenter-triggered retrain step is a reasonable P2 demonstration of the MLOps lifecycle if time allows.

---

## 8. Traffic Analysis

- **IP traffic:** Every observed packet is associated with source/destination IP, ports, protocol, and size — the only signals available without a return path.
- **Network flows:** Packets are grouped into flows by (source IP, destination IP) pairs over a sliding time window, since a single packet in isolation rarely carries enough signal.
- **Unidirectional communication:** All analysis is one-way by construction — the system never needs, requests, or waits for a response to characterize a flow.
- **Traffic patterns:** Baseline ("normal") patterns are learned per-source where possible; deviations in volume, timing regularity, or destination diversity are the primary signal of abnormal behavior.
- **Abnormal / suspicious activity:** Flagged when either the supervised model recognizes a known attack shape, or the anomaly model finds the flow statistically inconsistent with the learned normal baseline.

---

## 9. Threat Detection

| Category | Detection Objective | Relevant Traffic Behavior | Expected Output |
|---|---|---|---|
| **Port Scanning** | Detect reconnaissance against a single host | One source IP → one destination IP, many distinct destination ports, low bytes/packet | Category label, Medium–High severity |
| **Network/Host Scanning** | Detect reconnaissance across a subnet | One source IP → many destination IPs, consistent port/IAT pattern | Category label, Medium severity |
| **DDoS-like Volumetric Behavior** | Detect flooding intended to overwhelm a destination | High packet rate, low/uniform IAT, repetitive packet sizes | Category label, Critical severity |
| **Data Exfiltration (volume-anomaly based)** | Detect abnormal outbound data volume from an internal source | Unusually high byte count from a given source relative to its baseline | Category label, Critical severity |
| **C2-style Beaconing** | Detect periodic covert-channel-style communication | Low volume, rigid/periodic inter-arrival timing to a small set of destinations | "Unknown Anomaly" or "Beaconing" label, Medium severity |
| **Unknown Anomaly** | Catch-all for statistically abnormal traffic that doesn't match a known category | High anomaly-model deviation score, rare protocol/port combination | Label: Unknown Anomaly, severity per score |

**Disclaimer (carried into the product itself):** The system flags *indicators* consistent with these categories based on flow telemetry; it does not perform definitive attribution, and confidence scores should be read as decision support, not certainty.

---

## 10. Real-Time Detection Pipeline

```
Untrusted/Secure-Zone Traffic
        │  (through Data Diode — physically one-way)
        ▼
Passive Tap / Monitoring Interface  ──►  Simulator (demo) / PCAP Upload (offline)
        │
        ▼
Ingestion Listener (no send capability on this path)
        │
        ▼
Preprocessing & Validation (drop malformed, dedupe)
        │
        ▼
Windowed Feature Extraction (volume, timing, diversity)
        │
        ▼
Hybrid ML Scoring (Supervised classifier + Unsupervised anomaly model)
        │
        ▼
Risk Scoring & Severity Banding + Explanation Generation
        │
        ├──► Storage (flow + alert history)
        │
        └──► Live Dashboard / Alert Feed (push update)
```

---

## 11. Dashboard & User Experience

- **Main Dashboard:** System/listening status, total packets/flows scanned, current risk gauge, live traffic-volume line chart, threat-vs-safe donut chart, category breakdown.
- **Alert Feed:** Live-updating list of recent alerts with severity color-coding.
- **Alert Detail View:** Full flow metadata, risk score and severity, plain-language explanation, category label, and a short recent-history view for that source IP.
- **Alert History:** Searchable/filterable table (time range, category, severity, source IP) of past alerts — Time | Source IP | Category | Score | Status.
- **System Status:** Explicit indicator confirming the listener is passive-only (visually reinforces the "0 bytes sent back" guarantee — a meaningful trust signal for this specific product).
- **Simulator/Demo Panel:** Controls to start baseline traffic and trigger a named attack scenario.
- **Network Relationship View (P2):** Node/edge graph of source→destination activity, colored by risk.

Only UI elements that support triage, investigation, or the demo narrative are included — no unrelated enterprise chrome (user management, billing, etc.).

---

## 12. Alerts & Notifications

- **Alert condition:** Generated when a flow's combined risk score exceeds a configurable threshold (e.g., > 40 for Low/Medium visibility, with distinct Critical threshold e.g. > 80 for prominent UI treatment).
- **Severity bands:** 0–19 Informational · 20–39 Low · 40–59 Medium · 60–79 High · 80–100 Critical.
- **Alert fields:** Threat category, risk score, confidence, timestamp, source/destination metadata, supporting evidence (contributing features), plain-language explanation.
- **User actions:** Acknowledge, Mark as False Positive, Add Notes, view full evidence.
- **Alert lifecycle:** New → Acknowledged → (Investigating) → Resolved / False Positive.
- **Deduplication:** Repeated qualifying flows from the same source within a short window (e.g., 60 seconds) are aggregated into one alert with an updated last-seen time and event count, to avoid flooding the analyst.

---

## 13. Functional Requirements

| ID | Requirement |
|---|---|
| FR-001 | The system shall passively capture traffic from the monitoring interface without transmitting any packet back through that interface. |
| FR-002 | The system shall provide a synthetic traffic simulator capable of generating baseline traffic and injecting each threat category from Section 9 on demand. |
| FR-003 | The system shall accept an uploaded PCAP file and process it through the same pipeline as live traffic. |
| FR-004 | The system shall group packets into flows keyed by (source IP, destination IP) over a configurable sliding time window. |
| FR-005 | The system shall extract volume, timing, and diversity features per flow without inspecting packet payload contents. |
| FR-006 | The system shall drop and log packets missing required header fields rather than processing them. |
| FR-007 | The system shall score every flow with both a supervised classifier and an unsupervised anomaly model. |
| FR-008 | The system shall combine both model outputs into a single risk score between 0 and 100. |
| FR-009 | The system shall map every risk score to one of five severity bands. |
| FR-010 | The system shall assign a threat category label to a flow when the supervised model's confidence exceeds a defined threshold. |
| FR-011 | The system shall label a flow "Unknown Anomaly" when it is flagged primarily by the unsupervised model without a confident category match. |
| FR-012 | The system shall generate a human-readable explanation naming the top contributing features for every alert above the alerting threshold. |
| FR-013 | The system shall persist every generated alert with timestamp, category, score, explanation, and source flow reference. |
| FR-014 | The system shall display a live-updating dashboard reflecting current traffic volume, active alerts, and system status. |
| FR-015 | The system shall provide a searchable and filterable alert history view. |
| FR-016 | The system shall allow an analyst to mark an alert as Acknowledged or False Positive. |
| FR-017 | The system shall aggregate repeated qualifying flows from the same source within 60 seconds into a single alert with an incrementing event count. |
| FR-018 | The system shall display a persistent status indicator confirming the ingestion path has no outbound transmission capability. |
| FR-019 | The system shall never implement or expose any function capable of sending data back through the monitored interface. |
| FR-020 | The system shall complete flow-to-alert processing, from ingestion to dashboard display, in under 2 seconds under demo-scale load. |
| FR-021 | The system shall continue operating in a degraded mode (queuing flows, logging status) if the ML inference component becomes temporarily unavailable, rather than crashing. |
| FR-022 | The system shall log detection-relevant errors (malformed input, inference failure) in a structured, timestamped format. |

---

## 14. Non-Functional Requirements

- **Performance:** Alert should reach the dashboard within 2 seconds of the triggering flow being ingested, at demo-representative traffic volumes (hundreds of flows/second on commodity hardware).
- **Scalability:** MVP runs as a single local process/service; the pipeline (ingest → extract → score → store → push) is modular enough to later split across processes if higher throughput is needed — not required for MVP.
- **Reliability:** A failure in the ML component must not take down ingestion or the dashboard; it should degrade gracefully and recover automatically.
- **Security (of the tool itself):** No credentials or secrets in logs; if authentication is added, passwords must be hashed, not stored in plaintext.
- **Privacy:** No payload capture at any stage — feature extraction operates strictly on metadata, minimizing exposure of any sensitive content that might traverse the link.
- **Usability:** An analyst should be able to understand why an alert fired without needing ML background, via the plain-language explanation.
- **Maintainability:** Feature extraction, model inference, scoring, and presentation are kept as separable modules so any one can be modified or swapped independently.
- **Availability:** The system should run reliably offline/local for the full duration of a live demonstration, with no dependency on external network access.

---

## 15. Data Requirements

- **Input traffic data:** Timestamp, source IP, destination IP, source port, destination port, protocol, packet length.
- **Traffic/flow records:** Aggregated per-window flow records referencing their constituent packets.
- **Feature data:** Per-flow feature vectors, linked to their source flow record for traceability.
- **Detection results:** Model outputs (class probability, anomaly score), combined risk score, severity band, category label.
- **Alerts:** Category, score, confidence, timestamp, explanation, status, linked evidence (feature vector / flow).
- **Historical data:** Retained alert and flow-summary records for the dashboard's history view (raw packet payloads are never retained — see Non-Goals).
- **Metadata:** Correlation identifiers linking a packet → flow → feature vector → alert, so any alert can be traced back to its underlying evidence.

---

## 16. Dataset & Training Requirements

Public intrusion-detection datasets are naturally bidirectional (they capture full request/response conversations). To train models representative of a one-way link, source data must be preprocessed:

- **Selected approach:** Use a public labeled IDS dataset (e.g., CICIDS2017 / CSE-CIC-IDS2018, or a comparable alternative such as NSL-KDD/UNSW-NB15 if more convenient), split each bidirectional flow into its forward-direction half only, and strip any feature that depends on response/state information (e.g., TCP flags reflecting acknowledgement, response timing, retransmit counts). Only forward-flow metadata — packet counts, sizes, timing, ports, protocol — is retained as model input.
- **Why this approach:** It's the only way to legitimately train and evaluate a "unidirectional-aware" model using existing public data, rather than fabricating a dataset or claiming performance on data the model was never actually trained/tested on.
- **Unsupervised baseline:** The anomaly model is trained on the benign-labeled subset of the same forward-flow data, establishing what "normal" one-way traffic looks like statistically.
- **Class imbalance:** Attack classes are naturally rarer than benign traffic; standard resampling techniques (e.g., oversampling minority classes) may be applied during supervised training if the imbalance meaningfully hurts recall on rare categories.
- **Demo traffic:** The synthetic simulator (6.1) generates realistic-looking flow statistics for live demonstration, since real attacks cannot safely be run against the venue network. This is separate from, and does not replace, the dataset used for model training.

---

## 17. Success Metrics

| Metric | Target / Description |
|---|---|
| Detection accuracy (F1-score) | Target > 90% on held-out labeled test data — a goal to build toward, not a claimed achieved result until measured. |
| False positive rate | Target low false-positive rate on held-out benign traffic (specific target to be validated during testing, e.g. single-digit percent). |
| Detection/alert latency | Under 2 seconds from flow ingestion to alert appearing on the dashboard. |
| Explanation coverage | 100% of alerts above the alerting threshold include a feature-based explanation. |
| Processing throughput | Sustains demo-representative flow volume on a single laptop without dropped data. |

All figures above are **targets to validate**, not results to assert without measurement — no accuracy or FPR values should be presented as achieved unless they come from an actual evaluation run.

---

## 18. Security & Privacy Requirements

- The tool itself must not become a new attack surface: the monitoring tap sits strictly on the external/observation side, never inline with the diode, and never introduces a return path.
- No packet payload is ever captured, stored, or logged — only metadata, which structurally limits exposure of any sensitive information traversing the link.
- If any authentication is implemented for the dashboard, passwords must be hashed and sessions/tokens handled securely — kept minimal and simple for MVP rather than a full RBAC system.
- Any stored IPs/metadata should be treated as sensitive operational data and access-limited in a real deployment context.

---

## 19. System Constraints

- **Hardware:** Must run on a single student laptop for development and live demonstration — no dedicated server infrastructure assumed.
- **No physical diode:** The hardware data diode is simulated in software (e.g., a one-way queue or socket construction that structurally cannot read/receive), not built as real fiber-optic hardware.
- **Data constraints:** No access to real enterprise or classified traffic; the team relies on public datasets plus the synthetic simulator.
- **Model constraints:** Models are pre-trained offline before the demo; no live/online learning in MVP.
- **Real-time constraints:** Detection pipeline must comfortably fit within the sub-2-second latency target on modest hardware.
- **Development constraints:** Team is a 2nd-year B.Tech hackathon team with a fixed, short build window — architecture choices favor simplicity and one consistent language (Python) across ML and backend.
- **Hackathon constraints:** Must be demonstrable offline (no dependency on live internet or venue network reliability).

---

## 20. MVP Scope

### MVP (Must ship for SIH demonstration)
- Passive one-way ingestion listener + synthetic traffic simulator with at least the four core attack scenarios (port scan, flood/DDoS-like, exfiltration, beaconing/anomaly).
- Windowed feature extraction (volume, timing, diversity metrics).
- Hybrid detection: supervised classifier (Random Forest) + unsupervised anomaly model (Isolation Forest).
- Combined 0–100 risk score with severity banding.
- Feature-based plain-language explanation on every qualifying alert.
- Live dashboard: status, counters, traffic chart, threat/safe breakdown, alert feed.
- Alert history log with basic filtering.
- Visible confirmation that the ingestion path has zero outbound transmission.

### Post-MVP
- PCAP upload for offline analysis.
- Threat category classification surfaced with confidence.
- Network relationship graph view.
- Richer per-alert explainability (e.g., SHAP-style attribution).
- Basic authentication/login for the dashboard.
- Manual "simulate retraining" control to illustrate the MLOps lifecycle.

### Future Enhancements (Beyond SIH)
- Production-grade scaling (message queue, distributed inference workers, time-series-optimized storage).
- Role-based access control for multi-analyst teams.
- Continuous/online model retraining pipeline with versioning.
- Federated learning across multiple deployment sites without sharing raw flow data.
- Graph-based deep learning (e.g., GNNs) for lateral-movement-style pattern detection.
- Formal integration with downstream SOAR/ticketing systems (still detect-only; any action remains human-triggered outside this product).

---

## 21. User Stories

- As a **SOC analyst**, I want to see a live risk score for current traffic, so that I can immediately gauge whether the link is under active threat.
- As a **SOC analyst**, I want a plain-language reason attached to every alert, so that I can triage without needing to interpret raw model output.
  *Acceptance criteria:* Every alert above the threshold displays at least the top contributing feature(s) in plain language.
- As a **SOC analyst**, I want to mark an alert as a false positive, so that I can keep the active alert list focused on real threats.
- As a **network administrator**, I want to confirm the monitoring tool never sends anything back through the diode, so that I can be certain it doesn't weaken the diode's guarantee.
- As a **security team lead**, I want to review historical alerts by category and time range, so that I can identify recurring patterns or trends.
- As a **presenter/demo user**, I want to trigger a specific attack scenario on demand, so that I can reliably show detection working within a fixed demo window.
  *Acceptance criteria:* Selecting a scenario in the simulator panel produces a visible alert on the dashboard within 2 seconds.

---

## 22. Use Cases

- **UC1 — Detect Port/Network Scan:** Simulator or live traffic exhibits high port/destination diversity from a single source → system raises a Medium/High alert with scan-consistent explanation.
- **UC2 — Detect Volumetric Flood:** High packet rate with low, uniform inter-arrival time → system raises a Critical alert.
- **UC3 — Detect Exfiltration-style Volume Anomaly:** Source's outbound byte count spikes far above its learned baseline → system raises a Critical alert.
- **UC4 — Detect Unknown/Covert-Channel Anomaly:** Traffic doesn't match a known category but deviates statistically from baseline → system raises an "Unknown Anomaly" alert via the unsupervised model.
- **UC5 — Investigate an Alert:** Analyst clicks an alert, reviews flow metadata, score, and explanation, and marks it Acknowledged or False Positive.
- **UC6 — Review Historical Trends:** Security lead filters the alert history by category/date to review patterns over the monitoring period.
- **UC7 — Offline Analysis via PCAP (P1):** User uploads a capture file and receives the same scored output as live traffic would produce.

---

## 23. End-to-End Product Workflow

1. Traffic crosses the data diode and reaches the monitoring tap on the output side (or the simulator generates equivalent traffic for the demo).
2. The ingestion listener passively captures packets — no response is ever generated on this path.
3. Packets are validated, deduplicated, and grouped into flows over a sliding time window.
4. Feature extraction computes volume, timing, and diversity metrics per flow.
5. Both the supervised classifier and the unsupervised anomaly model score the flow.
6. Scores are combined into a single 0–100 risk score and mapped to a severity band; if above threshold, an explanation is generated from the contributing features.
7. The flow and any resulting alert are persisted to storage.
8. The dashboard updates live: counters and charts reflect the new flow; if an alert was generated, it appears in the alert feed with its severity, category (if confident), score, and explanation.
9. The analyst reviews the alert, inspects the evidence, and marks it Acknowledged or False Positive, closing the loop.

---

## 24. Feature Priority Matrix

| Feature | Priority |
|---|---|
| Passive ingestion + simulator | P0 |
| Windowed feature extraction | P0 |
| Hybrid detection (supervised + unsupervised) | P0 |
| Risk scoring & severity banding | P0 |
| Feature-based explanation | P0 |
| Live dashboard (status, charts, alert feed) | P0 |
| Alert history & filtering | P0 |
| Zero-outbound status indicator | P0 |
| PCAP upload | P1 |
| Threat category classification | P1 |
| Demo/simulation control panel | P1 |
| Richer XAI (SHAP-style) | P2 |
| Network relationship graph | P2 |
| Dashboard authentication | P2 |
| Manual "simulate retraining" control | P2 |

---

## 25. Assumptions

- A software-simulated data diode (a construct that structurally cannot receive/read) is an acceptable and faithful stand-in for the physical hardware diode in a hackathon prototype.
- Network metadata (source/destination IP, ports, protocol, size, timing) is reliably obtainable from the monitoring tap or simulator.
- Packet payloads are unavailable or encrypted, so detection must work on metadata alone.
- Public IDS datasets, once preprocessed to forward-flow-only features, are a reasonable proxy for real unidirectional traffic behavior.
- Models are trained offline prior to the demo; no live/online learning is required for MVP.
- The demo environment (laptop, no live enterprise traffic) is understood by judges as the standard hackathon constraint.

---

## 26. Risks & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Demo venue network/internet is unreliable | High | Run entirely locally; simulator and dashboard require no external connectivity. |
| Supervised model overfits to the training dataset and misses real-world variation | Medium | Rely on the unsupervised anomaly model as a complementary safety net for unseen patterns; validate with cross-validation. |
| High false-positive rate undermines analyst trust | Medium | Require score thresholds tuned against held-out benign data; support false-positive marking to track and (post-MVP) feed back into tuning. |
| Preprocessing public bidirectional datasets into forward-flow-only features removes too much signal, hurting accuracy | Medium | Validate feature set on held-out data before committing; keep feature set to metadata genuinely available on a one-way link so the demo claims stay honest. |
| Live packet capture proves too complex/unstable to build in the time available | Medium | Simulator and PCAP-replay paths provide a reliable fallback ingestion mode that doesn't depend on live capture working perfectly. |
| Team underestimates ML pipeline build time | Medium | Favor fast, well-understood models (Random Forest, Isolation Forest) over deep learning; scikit-learn implementations are quick to train and integrate. |

---

## 27. Future Enhancements

- Federated learning across multiple deployment sites, so models improve without any raw flow data leaving a site.
- Graph neural network-based detection for lateral-movement-style patterns across many hosts.
- Formal, versioned model retraining pipeline with performance tracking over time.
- Production-scale architecture (message queueing, distributed inference, time-series storage) for high-throughput enterprise deployments.
- Deeper explainability tooling (e.g., SHAP) for more precise, per-feature attribution on every alert.
- Optional read-only integration with downstream ticketing/SOAR systems for alert routing — while preserving the detect-only, non-active-response design of the core product.

---

## 28. Glossary

- **Data Diode:** A hardware device that physically enforces one-way data transfer, making it impossible for data to travel back into the protected network.
- **Unidirectional Traffic:** Network traffic that flows in only one direction between source and destination, with no observable or possible return path.
- **Covert Channel:** A method of transmitting information by encoding it into the timing, size, or pattern of otherwise legitimate traffic, rather than through an explicit payload.
- **Flow:** A group of packets sharing a source/destination pair (and often protocol/ports), aggregated over a time window for analysis.
- **Inter-Arrival Time (IAT):** The time gap between consecutive packets in a flow.
- **Isolation Forest:** An unsupervised machine learning algorithm that detects anomalies by measuring how easily a data point can be statistically "isolated" from the rest.
- **Random Forest:** A supervised machine learning algorithm that combines many decision trees to classify data, offering built-in feature-importance output.
- **Risk / Suspicion Score:** A 0–100 value representing how strongly a flow's characteristics resemble malicious or anomalous behavior.
- **False Positive:** An alert raised on traffic that is, in fact, benign.
- **PCAP:** A file format for storing captured network packet data, usable for offline analysis and testing.
- **Explainable AI (XAI):** Techniques for producing human-understandable reasons behind a model's prediction, rather than a bare score.
