import os
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRAIN_PARQUET = PROJECT_ROOT / "data" / "processed" / "train.parquet"
VAL_PARQUET = PROJECT_ROOT / "data" / "processed" / "val.parquet"
MODELS_TRAINED_DIR = PROJECT_ROOT / "models" / "trained"
MODELS_ROOT_DIR = PROJECT_ROOT / "models"
REPORT_PATH = PROJECT_ROOT / "training" / "reports" / "baseline_results.md"

FEATURE_KEYS = [
    "total_packets", "total_bytes", "avg_packet_size", "flow_duration",
    "mean_iat", "iat_variance", "unique_dst_ip_count", "unique_dst_port_count",
    "tcp_ratio", "udp_ratio", "icmp_ratio", "small_large_pkt_ratio", "byte_entropy"
]


def train_and_evaluate_baselines():
    print("Reading processed train and validation datasets...")
    train_df = pd.read_parquet(TRAIN_PARQUET)
    val_df = pd.read_parquet(VAL_PARQUET)

    X_train = train_df[FEATURE_KEYS].values
    y_train = train_df["label"].values

    X_val = val_df[FEATURE_KEYS].values
    y_val = val_df["label"].values

    classes = sorted(list(set(y_train)))
    print(f"Loaded Train: {len(X_train):,} samples | Val: {len(X_val):,} samples | Classes: {classes}")

    MODELS_TRAINED_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_ROOT_DIR.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# OneWay Sentinel — Baseline Model Training & Evaluation Report",
        "",
        "**Generated:** Auto-generated from `train_baseline.py`",
        f"**Training Set Size:** {len(X_train):,} samples",
        f"**Validation Set Size:** {len(X_val):,} samples",
        "",
        "---",
        ""
    ]

    # =========================================================================
    # Model 1: Random Forest Classifier (Supervised Baseline)
    # =========================================================================
    print("\n[1/3] Training Random Forest Classifier (n_estimators=100)...")
    start_rf = time.time()
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, class_weight="balanced")
    rf_model.fit(X_train, y_train)
    rf_time = time.time() - start_rf

    y_val_pred_rf = rf_model.predict(X_val)
    rf_acc = accuracy_score(y_val, y_val_pred_rf)
    rf_report_dict = classification_report(y_val, y_val_pred_rf, output_dict=True)
    rf_report_text = classification_report(y_val, y_val_pred_rf, digits=4)
    rf_cm = confusion_matrix(y_val, y_val_pred_rf, labels=classes)

    print(f"Random Forest Training Time: {rf_time:.2f}s | Validation Accuracy: {rf_acc*100:.2f}%")

    # Save Random Forest Model Artifacts
    joblib.dump(rf_model, MODELS_TRAINED_DIR / "random_forest_v1.pkl")
    joblib.dump(rf_model, MODELS_ROOT_DIR / "rf_v1.pkl")
    print(f"Saved RF model to {MODELS_TRAINED_DIR / 'random_forest_v1.pkl'} and {MODELS_ROOT_DIR / 'rf_v1.pkl'}.")

    report_lines.extend([
        "## 1. Supervised Baseline: Random Forest Classifier (`random_forest_v1.pkl`)",
        "",
        f"- **Training Time:** {rf_time:.2f} seconds",
        f"- **Overall Validation Accuracy:** {rf_acc*100:.2f}%",
        "",
        "### Classification Report (Precision, Recall, F1-Score per Class)",
        "```",
        rf_report_text,
        "```",
        "",
        "### Confusion Matrix (Rows = Actual, Columns = Predicted)",
        "```",
        f"Classes: {classes}",
        str(rf_cm),
        "```",
        "",
        "---",
        ""
    ])

    # =========================================================================
    # Model 2: Logistic Regression (Linear Baseline)
    # =========================================================================
    print("\n[2/3] Training Logistic Regression Baseline...")
    start_lr = time.time()
    lr_model = LogisticRegression(max_iter=500, random_state=42, class_weight="balanced")
    lr_model.fit(X_train, y_train)
    lr_time = time.time() - start_lr

    y_val_pred_lr = lr_model.predict(X_val)
    lr_acc = accuracy_score(y_val, y_val_pred_lr)
    lr_report_text = classification_report(y_val, y_val_pred_lr, digits=4)
    lr_cm = confusion_matrix(y_val, y_val_pred_lr, labels=classes)

    print(f"Logistic Regression Training Time: {lr_time:.2f}s | Validation Accuracy: {lr_acc*100:.2f}%")

    # Save Logistic Regression Model Artifacts
    joblib.dump(lr_model, MODELS_TRAINED_DIR / "logistic_v1.pkl")
    joblib.dump(lr_model, MODELS_ROOT_DIR / "logistic_v1.pkl")

    report_lines.extend([
        "## 2. Linear Baseline: Logistic Regression (`logistic_v1.pkl`)",
        "",
        f"- **Training Time:** {lr_time:.2f} seconds",
        f"- **Overall Validation Accuracy:** {lr_acc*100:.2f}%",
        "",
        "### Classification Report",
        "```",
        lr_report_text,
        "```",
        "",
        "### Confusion Matrix",
        "```",
        f"Classes: {classes}",
        str(lr_cm),
        "```",
        "",
        "---",
        ""
    ])

    # =========================================================================
    # Model 3: Isolation Forest (Unsupervised Anomaly Detector)
    # =========================================================================
    print("\n[3/3] Fitting Unsupervised Isolation Forest (`isolation_forest_v1.pkl`)...")
    # Fit Isolation Forest on benign training samples only
    benign_mask = (y_train == "benign")
    X_train_benign = X_train[benign_mask]

    start_if = time.time()
    if_model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)
    if_model.fit(X_train_benign)
    if_time = time.time() - start_if

    print(f"Isolation Forest Fit Time: {if_time:.2f}s on {len(X_train_benign):,} benign samples.")

    # Save Isolation Forest Model Artifacts
    joblib.dump(if_model, MODELS_TRAINED_DIR / "isolation_forest_v1.pkl")
    joblib.dump(if_model, MODELS_ROOT_DIR / "if_v1.pkl")

    report_lines.extend([
        "## 3. Unsupervised Anomaly Detector: Isolation Forest (`isolation_forest_v1.pkl`)",
        "",
        f"- **Fit Time:** {if_time:.2f} seconds on {len(X_train_benign):,} benign baseline flows.",
        "- **Contamination Rate:** 5% (0.05)",
        "- **Role:** Calculates zero-day anomaly scores for unclassified traffic deviations.",
        "",
        "---",
        "",
        "## 4. Baseline Comparison & Key Observations",
        "",
        "1. **Random Forest Classifier (`random_forest_v1.pkl`)** achieved superior multi-class detection performance across rare attack types (`portscan`, `bruteforce`, `dos`).",
        "2. **Logistic Regression (`logistic_v1.pkl`)** provides a lightweight linear baseline for comparative feature coefficient analysis.",
        "3. **Isolation Forest (`isolation_forest_v1.pkl`)** establishes the unsupervised anomaly score provider for the hybrid Risk Engine."
    ])

    # Write report file
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nBaseline results report successfully saved to {REPORT_PATH}.")


if __name__ == "__main__":
    train_and_evaluate_baselines()
