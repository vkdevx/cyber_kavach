# OneWay Sentinel — Acceptance Test Criteria Matrix (`acceptance.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`master-prd.md:268`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/master-prd.md#L268) and [`rules.md:788`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L788).

---

## 1. Functional Requirements Acceptance Matrix (FR-001 to FR-022)

| Requirement ID | Requirement Summary | Acceptance Criteria | Verification Method | Pass/Fail Criteria |
|---|---|---|---|---|
| **FR-001** | Passive One-Way Ingestion | Capture interface receives network packets without transmitting any packet back. | Execution of `scripts/verify_zero_outbound.py` and `tests/network/test_zero_outbound.py`. | **PASS:** Zero bytes written to capture socket across entire test run. |
| **FR-002** | Synthetic Traffic Simulator | Generate normal traffic baseline and inject all 6 attack scenarios on demand. | Trigger each scenario via `SimulatorControls` UI panel. | **PASS:** Visible alert appears on dashboard within 2 seconds. |
| **FR-003** | PCAP Upload Analysis | Upload `.pcap` capture file and process through feature extraction & scoring. | Upload sample `.pcap` via `PcapUploadModal`. | **PASS:** Scored flows and alerts populated with `source = 'pcap'`. |
| **FR-004** | Flow Aggregation | Group packets by `(src_ip, dst_ip, src_port, dst_port, protocol)` over 5s sliding window. | Unit test in `tests/network/test_passive_ingestion.py`. | **PASS:** Packet sequences grouped accurately into single `FlowRecord`. |
| **FR-005** | Payload-Free Feature Extraction | Extract 13 numerical volume, timing, and diversity features without payload inspection. | Inspection of `ml/feature_extraction.py` and database `features` table. | **PASS:** Zero payload bytes retained or persisted; 13 features calculated. |
| **FR-006** | Malformed Packet Dropping | Drop packets missing required IP/TCP/UDP header fields and log event. | Pass truncated packet bytes to `packet_validator.py`. | **PASS:** Invalid packet dropped; structured error log recorded. |
| **FR-007** | Dual Model Scoring | Score every flow using Random Forest Classifier and Isolation Forest. | Unit test in `tests/ml/test_random_forest_inference.py`. | **PASS:** RF class probability and IF anomaly score returned for every flow. |
| **FR-008** | Single Risk Score Fusion | Fuse RF probability and IF anomaly score into 0-100 risk score. | Unit test in `tests/unit/test_risk_engine.py`. | **PASS:** Integer risk score in [0, 100] calculated according to fusion formula. |
| **FR-009** | Severity Banding | Map risk score to 5 severity bands (Informational, Low, Medium, High, Critical). | Boundary tests in `tests/unit/test_severity_mapper.py` at 19/20, 39/40, 59/60, 79/80. | **PASS:** Exact severity string mapped per risk score threshold. |
| **FR-010** | Threat Category Labeling | Assign category label when RF probability $\ge 0.70$. | Test scenario flows against supervised model. | **PASS:** Specific threat category label assigned to alert record. |
| **FR-011** | Unknown Anomaly Labeling | Label flow `Unknown Anomaly` when IF score $\ge 0.65$ without confident RF match. | Inject unclassified outlier flow into pipeline. | **PASS:** Alert generated with category `Unknown Anomaly`. |
| **FR-012** | Plain-Language Explanations | Generate 2-3 line feature-importance explanation for every qualifying alert. | Inspect `explainer.py` output on generated alerts. | **PASS:** 100% of alerts > threshold contain plain-language feature explanation. |
| **FR-013** | Alert Persistence | Store generated alerts with timestamp, score, category, and explanation. | Query SQLite `alerts` table post-alert generation. | **PASS:** Complete alert row persisted with matching `correlation_id`. |
| **FR-014** | Live Dashboard | Display status, counters, volume line chart, threat donut chart, and live feed. | Visual inspection of `MainDashboard.jsx` during stream. | **PASS:** Real-time updates pushed via WebSocket without page reload. |
| **FR-015** | Alert History Filtering | Search and filter alert log by date range, category, severity, src IP, status. | Execute queries on `AlertHistory.jsx` filter bar. | **PASS:** Table updates with correctly filtered subset of alerts. |
| **FR-016** | Analyst Triage Actions | Mark alert status as `acknowledged` or `false_positive` with notes. | Click triage buttons on `AlertDetail.jsx` / `CyberTable`. | **PASS:** Database `alerts.status` updated in place. |
| **FR-017** | 60-Second Alert Aggregation| Repeated qualifying flows from same source within 60s update event count. | Inject 5 identical attack flows within 30s. | **PASS:** Single alert record updated with incremented event counter. |
| **FR-018** | Zero-Outbound Badge | Display permanent `ZeroOutboundBadge` trust indicator confirming passive mode. | Visual inspection of `Sidebar.jsx` and `StatusBar.jsx`. | **PASS:** Badge permanently rendered; reflects `/api/status` check. |
| **FR-019** | Strict Non-Transmission | No code path implements send capability on capture interface. | Automated static grep check (`scripts/verify_zero_outbound.py`). | **PASS:** Zero instances of `send`, `sendp`, `sr`, `sr1`, or raw write calls. |
| **FR-020** | Sub-2s Latency Budget | Flow-to-alert processing latency from packet capture to WS dashboard push <2s. | Performance benchmark in `tests/integration/test_pipeline_end_to_end.py`. | **PASS:** Mean end-to-end latency $< 1.5$ seconds under demo load. |
| **FR-021** | Graceful Degraded Mode | System continues operating with `severity="Unknown - ML Unavailable"` if ML fails. | Mock exception in `inference_service.py`. | **PASS:** Pipeline stays alive; dashboard alerts rendered with degraded flag. |
| **FR-022** | Structured Audit Logging | Log all detection-relevant errors in structured ISO-timestamped JSON. | Inspect log files generated by `backend/core/logging_setup.py`. | **PASS:** Log entries contain required structured fields and correlation IDs. |

---

## 2. Non-Functional Requirements (NFR) Acceptance

1. **Performance Target:** End-to-end flow ingestion to dashboard push latency $< 2.0$ seconds on a commodity laptop.
2. **Zero Outbound Guarantee:** Absolute zero return transmission through monitored link. Enforced structurally (one-directional queue), procedurally (`interface_guard.py`), and empirically (`verify_zero_outbound.py`).
3. **Data Privacy:** Zero packet payload bytes captured, stored, or logged at any stage.
4. **Offline Dependability:** Complete demonstration operates 100% offline without live internet access or external API dependencies.
