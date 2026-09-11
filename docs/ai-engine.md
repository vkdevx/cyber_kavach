# OneWay Sentinel — Hybrid AI/ML Engine Specification (`ai-engine.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`master-prd.md:157`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/master-prd.md#L157), [`architecture.md:402`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md#L402), and [`rules.md:158`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L158).

---

## 1. AI/ML Pipeline Overview

OneWay Sentinel implements a **hybrid machine learning architecture** designed specifically for unidirectional IP traffic monitoring. Because one-way data links lack TCP handshakes, retransmissions, or response packets, conventional stateful detection fails. The AI engine operates strictly on statistical flow metadata extracted over sliding time windows.

```
FlowRecord (network/)
        │
        ▼
Feature Extraction (ml/feature_extraction.py) ──► 13-feature Vector
        │
        ▼
Feature Normalization (ml/feature_normalizer.py) ──► Per-Source Normalization
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
Supervised Classifier                   Unsupervised Anomaly Model
(RandomForestClassifier)                 (IsolationForest)
        │                                      │
        ▼ (class, probability)                 ▼ (anomaly_score)
        └──────────────────┬───────────────────┘
                           ▼
                  Score Fusion Engine (ml/fusion/score_fusion.py)
                           │
                           ▼
               Risk Engine & Severity Mapper (backend/risk/)
                           │
                           ▼ (0-100 score, severity, category, confidence, explanation)
                Alert Record / Dashboard Push
```

---

## 2. Feature Extraction Engine (13 Numerical Features)

Packets are grouped into unidirectional flows by `(src_ip, dst_ip, src_port, dst_port, protocol)` over a sliding time window (default 5 seconds). `ml/feature_extraction.py` extracts a fixed 13-dimensional numeric vector:

| # | Feature Name | Description & Formula | Threat Relevance |
|---|---|---|---|
| 1 | `total_packets` | Count of packets observed in the flow window. | High packet rates indicate volumetric flooding. |
| 2 | `total_bytes` | Total payload and header bytes observed. | Spikes indicate exfiltration or large file transfers. |
| 3 | `avg_packet_size` | `total_bytes / total_packets`. | Small average size indicates scans/pings; large indicates exfiltration. |
| 4 | `flow_duration` | `last_packet_ts - first_packet_ts` (seconds). | Measures flow longevity within the window. |
| 5 | `mean_iat` | Average inter-arrival time between packets: $\frac{1}{N-1} \sum \Delta t_i$. | Rigid/fixed IAT indicates automated C2 beaconing. |
| 6 | `iat_variance` | Variance of packet inter-arrival times: $\text{Var}(\Delta t)$. | Near-zero variance signals automated script activity. |
| 7 | `unique_dst_ip_count` | Number of distinct destination IPs contacted by `src_ip` in window. | High count indicates subnet/network scanning. |
| 8 | `unique_dst_port_count` | Number of distinct destination ports contacted by `src_ip` in window. | High count indicates port scanning. |
| 9 | `tcp_ratio` | Proportion of TCP packets in window ($N_{\text{tcp}} / N_{\text{total}}$). | Protocol distribution shift. |
| 10 | `udp_ratio` | Proportion of UDP packets in window ($N_{\text{udp}} / N_{\text{total}}$). | Volumetric UDP flood detection. |
| 11 | `icmp_ratio` | Proportion of ICMP packets in window ($N_{\text{icmp}} / N_{\text{total}}$). | Ping sweep detection. |
| 12 | `small_large_pkt_ratio` | Ratio of packets $<128$ bytes to packets $>1024$ bytes. | Structural traffic asymmetry. |
| 13 | `byte_entropy` | Shannon entropy of packet lengths across the flow: $-\sum p_i \log_2(p_i)$. | Uniform/encrypted covert channel detection. |

---

## 3. Hybrid ML Models

### 3.1 Supervised Model: Random Forest Classifier
- **Implementation:** `sklearn.ensemble.RandomForestClassifier` (100 trees, `max_depth=15`).
- **Artifact:** `models/trained/random_forest_v1.pkl`
- **Training Data:** Labeled flow data from public IDS datasets (CICIDS2017 / CSE-CIC-IDS2018), filtered to forward-flow metadata only.
- **Classes:** `Benign`, `Port Scanning`, `Network Scanning`, `DDoS-like Volumetric Behavior`, `Data Exfiltration`, `Beaconing`.
- **Output:** Predicted threat class and confidence probability ($P_{\text{RF}} \in [0.0, 1.0]$).

### 3.2 Unsupervised Anomaly Detector: Isolation Forest
- **Implementation:** `sklearn.ensemble.IsolationForest` (`contamination=0.05`, `n_estimators=100`).
- **Artifact:** `models/trained/isolation_forest_v1.pkl`
- **Training Data:** Exclusively benign forward-flow baseline traffic.
- **Output:** Raw decision function anomaly score, normalized to $S_{\text{IF}} \in [0.0, 1.0]$ (where values near 1.0 represent extreme statistical outliers).

---

## 4. Score Fusion & Risk Engine Mathematics

`ml/fusion/score_fusion.py` and `backend/risk/risk_engine.py` combine the model outputs into a unified 0–100 risk score:

### Fusion Policy:
1. **Classification Selection:**
   - If $P_{\text{RF}} \ge 0.70$ for a non-benign attack class $\rightarrow$ Label as that specific threat category (e.g. `Port Scanning`).
   - Else if $S_{\text{IF}} \ge 0.65$ (statistically anomalous but unclassified by RF) $\rightarrow$ Label as `Unknown Anomaly` (or `Beaconing` if IAT variance is near zero).
   - Else $\rightarrow$ Label as `Benign`.

2. **Risk Score Formula:**
   $$\text{Risk Score} = \min\left(100, \text{Round}\left(100 \times \left( w_{\text{RF}} \cdot P_{\text{RF\_attack}} + w_{\text{IF}} \cdot S_{\text{IF}} \right) \right)\right)$$
   Where $w_{\text{RF}} = 0.60$ and $w_{\text{IF}} = 0.40$ (configured in `config/risk_weights.yaml`).

3. **Severity Band Mapping (`backend/risk/severity_mapper.py`):**
   - **0 – 19:** `Informational`
   - **20 – 39:** `Low`
   - **40 – 59:** `Medium`
   - **60 – 79:** `High`
   - **80 – 100:** `Critical`

---

## 5. Model Confidence & Explanation Generation

### 5.1 Confidence Engine (`backend/risk/confidence_engine.py`)
Computes model concordance:
$$\text{Confidence} = \frac{P_{\text{RF}} + (1.0 - |P_{\text{RF}} - S_{\text{IF}}|)}{2.0}$$

### 5.2 Explainer Engine (`backend/risk/explainer.py`)
Generates 2–3 line human-readable text explanations by querying Random Forest `feature_importances_` and calculating per-feature $Z$-scores relative to the source baseline:
- *Example (Port Scan):* `"Destination port diversity is 9x the learned baseline (47 unique ports in 5s); inter-arrival time is tight (mean IAT: 1.2ms)."`
- *Example (Exfiltration):* `"Outbound volume spiked to 14.2 MB in 5 seconds (12x baseline); packet size skewed heavily to maximum MTU."`

---

## 6. Dataset Preprocessing & Forward-Flow Filtering

Public IDS datasets (CICIDS2017 / CSE-CIC-IDS2018) contain bidirectional flow features (TCP ACK flags, response counts, backward packet headers). `datasets/pipeline/forward_flow_filter.py` strips all response-dependent features:

1. **Discarded:** `Bwd Packet Length Max`, `Fwd IAT Std`, `FIN Flag Count`, `SYN Flag Count` (reverse), `ACK Flag Count`, `Down/Up Ratio`, `Average Packet Size` (bidirectional).
2. **Retained:** Forward packet counts, forward byte totals, forward inter-arrival times, destination IP/port counts, header-based protocol flags.

---

## 7. Retraining & Model Lifecycle Procedure

When new attack samples or live network traffic captures are collected, follow this step-by-step procedure to update and deploy a refreshed ML model without downtime or silent model overwrite.

### 7.1 Ingesting & Labeling New Data
1. Place raw PCAPs or PCAP flow exports into `/data/raw/live_captures/` or `/data/raw/custom_attacks/`.
2. Run the schema unification script to extract 13-feature vectors and map taxonomy labels:
   ```bash
   python scripts/data_prep/unify_schema.py
   ```
   Output: Updated `/data/processed/unified_dataset.parquet`.

### 7.2 Preprocessing & Feature Scaling
1. Re-fit `StandardScaler` and generate 70% / 15% / 15% stratified train/val/test splits:
   ```bash
   python scripts/data_prep/preprocess.py
   ```
   Output: Refreshed `/data/processed/train.parquet`, `val.parquet`, `test.parquet`, and `/models/trained/scaler.pkl`.

### 7.3 Baseline Training & Hyperparameter Tuning
1. Train candidate baseline classifiers:
   ```bash
   python training/scripts/train_baseline.py
   ```
2. Run hyperparameter tuning (`RandomizedSearchCV`) optimizing for attack class recall and weighted F1-score:
   ```bash
   python training/scripts/tune_model.py
   ```
3. Verify holdout test performance with single-pass evaluation:
   ```bash
   python training/scripts/evaluate_final_test.py
   ```

### 7.4 Model Versioning Convention & Production Export
1. **Versioning Syntax:** Never overwrite existing working models directly. Save new model artifacts with semantic versioning:
   - `/models/trained/threat_classifier_v1.1.pkl`
   - `/models/trained/scaler_v1.1.pkl`
2. **Registry Resolution (`ml/model_registry.py`):** ModelRegistry dynamically probes `/models/trained/` prioritizing explicit versioned files (`threat_classifier_final.pkl` or highest versioned candidate) while maintaining automatic fallback to embedded dummy predictors.
3. **Verification:** Execute `python -m pytest tests/unit/ tests/integration/` to verify zero regression across end-to-end telemetry and PCAP detection pipelines.
