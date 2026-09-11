import os
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PARQUET_PATH = PROJECT_ROOT / "data" / "processed" / "unified_dataset.parquet"
REPORT_PATH = PROJECT_ROOT / "training" / "reports" / "eda_report.md"


def run_eda():
    print(f"Reading unified dataset from {PARQUET_PATH}...")
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(f"Parquet file {PARQUET_PATH} does not exist. Run unify_schema.py first.")

    df = pd.read_parquet(PARQUET_PATH)
    total_records = len(df)
    print(f"Loaded {total_records:,} total records.")

    feature_cols = [
        "total_packets", "total_bytes", "avg_packet_size", "flow_duration",
        "mean_iat", "iat_variance", "unique_dst_ip_count", "unique_dst_port_count",
        "tcp_ratio", "udp_ratio", "icmp_ratio", "small_large_pkt_ratio", "byte_entropy"
    ]

    # 1. Overall Class Balance
    class_counts = df["label"].value_counts()
    class_pcts = (class_counts / total_records) * 100.0

    class_balance_str = "| Label | Count | Percentage | Class Imbalance Ratio |\n|---|---|---|---|\n"
    benign_count = class_counts.get("benign", 1)

    for label, count in class_counts.items():
        pct = class_pcts[label]
        ratio = f"1 : {benign_count / max(1, count):.1f}" if label != "benign" else "Baseline (1.0)"
        class_balance_str += f"| `{label}` | {count:,} | {pct:.2f}% | {ratio} |\n"

    # 2. Source Dataset breakdown
    source_counts = df["dataset_source"].value_counts()
    source_breakdown_str = "| Source Dataset | Record Count | Percentage |\n|---|---|---|\n"
    for src, count in source_counts.items():
        source_breakdown_str += f"| `{src}` | {count:,} | {(count/total_records)*100.0:.2f}% |\n"

    # Source class pivot markdown table
    source_class_pivot = pd.crosstab(df["dataset_source"], df["label"], margins=True)
    pivot_md = "| Dataset Source | " + " | ".join(source_class_pivot.columns) + " |\n"
    pivot_md += "|---| " + " | ".join(["---"] * len(source_class_pivot.columns)) + " |\n"
    for idx, row in source_class_pivot.iterrows():
        pivot_md += f"| `{idx}` | " + " | ".join([f"{v:,}" for v in row.values]) + " |\n"

    # 3. Feature Summary Statistics
    stats_df = df[feature_cols].describe().T[["mean", "std", "min", "50%", "max"]]
    stats_md = "| Feature Name | Mean | Std Dev | Min | Median | Max |\n|---|---|---|---|---|---|\n"
    for idx, row in stats_df.iterrows():
        stats_md += f"| `{idx}` | {row['mean']:.3f} | {row['std']:.3f} | {row['min']:.3f} | {row['50%']:.3f} | {row['max']:.3f} |\n"

    # 4. Constant / Near-Constant Features & Correlation Analysis
    variances = df[feature_cols].var()
    constant_features = [col for col, var in variances.items() if var == 0 or pd.isna(var)]
    low_variance_features = [col for col, var in variances.items() if 0 < var < 1e-4]

    corr_matrix = df[feature_cols].corr().abs()
    high_corr_pairs = []

    for i in range(len(feature_cols)):
        for j in range(i + 1, len(feature_cols)):
            f1, f2 = feature_cols[i], feature_cols[j]
            val = corr_matrix.loc[f1, f2]
            if val > 0.85:
                high_corr_pairs.append((f1, f2, val))

    corr_pairs_str = "| Feature 1 | Feature 2 | Absolute Correlation |\n|---|---|---|\n"
    if high_corr_pairs:
        for f1, f2, val in high_corr_pairs:
            corr_pairs_str += f"| `{f1}` | `{f2}` | {val:.3f} |\n"
    else:
        corr_pairs_str += "| None | None | No pairs > 0.85 |\n"

    # 5. Generate Markdown Report
    report_content = f"""# OneWay Sentinel — Exploratory Data Analysis (EDA) Report

**Generated:** Auto-generated from `unified_dataset.parquet`  
**Dataset Path:** `{PARQUET_PATH}`  
**Total Records:** {total_records:,}  

---

## 1. Class Balance & Taxonomy Distribution

Benign traffic accounts for **{class_pcts.get('benign', 0):.2f}%** of the unified dataset. Minority attack classes like `u2r` ({class_counts.get('u2r', 0)} samples) and `portscan` ({class_counts.get('portscan', 0)} samples) exhibit severe class imbalance requiring SMOTE or class-weighted loss during model training.

{class_balance_str}

### Breakdown by Source Dataset

{source_breakdown_str}

### Cross-Tabulation (Dataset Source vs. Class Label)

{pivot_md}

---

## 2. Feature Summary Statistics (13 Shared Features)

{stats_md}

---

## 3. Correlation & Constant Feature Analysis

### Constant / Low-Variance Features
- **Zero Variance / Constant Features:** {constant_features if constant_features else "None (All 13 features show positive variance)"}
- **Low Variance (< 0.0001):** {low_variance_features if low_variance_features else "None"}

### Highly Correlated Feature Pairs (|r| > 0.85)
{corr_pairs_str}

---

## 4. Class Imbalance Severity Assessment

1. **Severe Imbalance Warning:** `benign` traffic comprises over {class_pcts.get('benign', 0):.1f}% of total samples. `u2r` represents only {class_pcts.get('u2r', 0)/total_records*100.0:.4f}% of data.
2. **Mitigation Strategy:**
   - Use `class_weight='balanced'` in Random Forest training.
   - Apply SMOTE or RandomOverSampler on minority classes (`u2r`, `r2l`, `portscan`) during offline training pipelines.
   - Evaluate using Precision, Recall, F1-Score, and ROC-AUC per class (never raw Accuracy alone).
"""

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"EDA report successfully saved to {REPORT_PATH}.")


if __name__ == "__main__":
    run_eda()
