# OneWay Sentinel — Exploratory Data Analysis (EDA) Report

**Generated:** Auto-generated from `unified_dataset.parquet`  
**Dataset Path:** `C:\Users\KCFL-4\Desktop\CyberThreatDetection\data\processed\unified_dataset.parquet`  
**Total Records:** 422,544  

---

## 1. Class Balance & Taxonomy Distribution

Benign traffic accounts for **89.72%** of the unified dataset. Minority attack classes like `u2r` (37 samples) and `portscan` (234 samples) exhibit severe class imbalance requiring SMOTE or class-weighted loss during model training.

| Label | Count | Percentage | Class Imbalance Ratio |
|---|---|---|---|
| `benign` | 379,086 | 89.72% | Baseline (1.0) |
| `dos` | 33,691 | 7.97% | 1 : 11.3 |
| `bruteforce` | 6,424 | 1.52% | 1 : 59.0 |
| `probe` | 2,104 | 0.50% | 1 : 180.2 |
| `r2l` | 968 | 0.23% | 1 : 391.6 |
| `portscan` | 234 | 0.06% | 1 : 1620.0 |
| `u2r` | 37 | 0.01% | 1 : 10245.6 |


### Breakdown by Source Dataset

| Source Dataset | Record Count | Percentage |
|---|---|---|
| `CICIDS2017` | 400,000 | 94.66% |
| `NSL-KDD` | 22,544 | 5.34% |


### Cross-Tabulation (Dataset Source vs. Class Label)

| Dataset Source | benign | bruteforce | dos | portscan | probe | r2l | u2r | All |
|---| --- | --- | --- | --- | --- | --- | --- | --- |
| `CICIDS2017` | 368,045 | 5,193 | 26,526 | 234 | 2 | 0 | 0 | 400,000 |
| `NSL-KDD` | 11,041 | 1,231 | 7,165 | 0 | 2,102 | 968 | 37 | 22,544 |
| `All` | 379,086 | 6,424 | 33,691 | 234 | 2,104 | 968 | 37 | 422,544 |


---

## 2. Feature Summary Statistics (13 Shared Features)

| Feature Name | Mean | Std Dev | Min | Median | Max |
|---|---|---|---|---|---|
| `total_packets` | 68.323 | 4471.063 | 1.000 | 4.000 | 511681.000 |
| `total_bytes` | 72723.989 | 5797837.377 | 0.000 | 233.000 | 656776408.000 |
| `avg_packet_size` | 622.619 | 109353.139 | 0.000 | 81.000 | 62916124.000 |
| `flow_duration` | 26.791 | 329.903 | -0.000 | 0.061 | 57715.000 |
| `mean_iat` | 11.571 | 324.429 | -0.000 | 0.027 | 57715.000 |
| `iat_variance` | 64.062 | 346.290 | 0.000 | 0.000 | 7191.040 |
| `unique_dst_ip_count` | 0.986 | 0.112 | 0.000 | 1.000 | 1.000 |
| `unique_dst_port_count` | 0.952 | 0.212 | 0.000 | 1.000 | 1.000 |
| `tcp_ratio` | 0.991 | 0.093 | 0.000 | 1.000 | 1.000 |
| `udp_ratio` | 0.006 | 0.079 | 0.000 | 0.000 | 1.000 |
| `icmp_ratio` | 0.002 | 0.050 | 0.000 | 0.000 | 1.000 |
| `small_large_pkt_ratio` | 0.319 | 0.359 | 0.000 | 0.210 | 1.000 |
| `byte_entropy` | 5.728 | 3.317 | 0.000 | 8.000 | 8.000 |


---

## 3. Correlation & Constant Feature Analysis

### Constant / Low-Variance Features
- **Zero Variance / Constant Features:** None (All 13 features show positive variance)
- **Low Variance (< 0.0001):** None

### Highly Correlated Feature Pairs (|r| > 0.85)
| Feature 1 | Feature 2 | Absolute Correlation |
|---|---|---|
| `total_packets` | `total_bytes` | 0.996 |
| `flow_duration` | `mean_iat` | 0.986 |


---

## 4. Class Imbalance Severity Assessment

1. **Severe Imbalance Warning:** `benign` traffic comprises over 89.7% of total samples. `u2r` represents only 0.0000% of data.
2. **Mitigation Strategy:**
   - Use `class_weight='balanced'` in Random Forest training.
   - Apply SMOTE or RandomOverSampler on minority classes (`u2r`, `r2l`, `portscan`) during offline training pipelines.
   - Evaluate using Precision, Recall, F1-Score, and ROC-AUC per class (never raw Accuracy alone).
