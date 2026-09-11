import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PARQUET_INPUT = PROJECT_ROOT / "data" / "processed" / "unified_dataset.parquet"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models" / "trained"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
SCALER_ALT_PATH = PROJECT_ROOT / "models" / "scaler.pkl"

FEATURE_KEYS = [
    "total_packets", "total_bytes", "avg_packet_size", "flow_duration",
    "mean_iat", "iat_variance", "unique_dst_ip_count", "unique_dst_port_count",
    "tcp_ratio", "udp_ratio", "icmp_ratio", "small_large_pkt_ratio", "byte_entropy"
]


def oversample_minority_classes(X_scaled: np.ndarray, y: pd.Series, min_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Native random oversampling for minority classes (u2r, portscan, r2l)
    to ensure effective model representation without external dependencies.
    """
    df_temp = pd.DataFrame(X_scaled, columns=FEATURE_KEYS)
    df_temp["label"] = y.values

    oversampled_frames = []
    class_counts = df_temp["label"].value_counts()

    for cls, count in class_counts.items():
        cls_df = df_temp[df_temp["label"] == cls]
        if count < min_samples:
            num_to_add = min_samples - count
            resampled = cls_df.sample(n=num_to_add, replace=True, random_state=42)
            oversampled_frames.append(cls_df)
            oversampled_frames.append(resampled)
        else:
            oversampled_frames.append(cls_df)

    res_df = pd.concat(oversampled_frames, ignore_index=True)
    return res_df[FEATURE_KEYS].to_numpy(), res_df["label"].to_numpy()


def preprocess_and_split():
    print(f"Reading unified dataset from {PARQUET_INPUT}...")
    if not PARQUET_INPUT.exists():
        raise FileNotFoundError(f"Input file {PARQUET_INPUT} not found. Run unify_schema.py first.")

    df = pd.read_parquet(PARQUET_INPUT)
    print(f"Loaded {len(df):,} total records.")

    # 1. Feature selection & validation
    X = df[FEATURE_KEYS].copy()
    y = df["label"].copy()

    # 2. Stratified Train (70%) / Val (15%) / Test (15%) split
    print("Performing 70% / 15% / 15% stratified train/val/test split...")
    X_train_raw, X_temp, y_train_raw, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val_raw, X_test_raw, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    print(f"Raw Split Sizes -> Train: {len(X_train_raw):,}, Val: {len(X_val_raw):,}, Test: {len(X_test_raw):,}")

    # 3. Fit StandardScaler on Train split only (to avoid data leakage)
    print("Fitting StandardScaler on training data...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_val_scaled = scaler.transform(X_val_raw)
    X_test_scaled = scaler.transform(X_test_raw)

    # Save fitted scaler artifact
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(scaler, SCALER_ALT_PATH)
    print(f"Fitted StandardScaler saved to {SCALER_PATH} and {SCALER_ALT_PATH}.")

    # 4. Handle Class Imbalance on Training Split
    # Choice: Native random oversampling is used to boost extreme minority classes (u2r, portscan, r2l)
    # up to a minimum of 5,000 samples per class in training set without synthesizing out-of-bounds float values.
    print("Applying random oversampling on training split minority classes...")
    X_train_resampled, y_train_resampled = oversample_minority_classes(X_train_scaled, y_train_raw, min_samples=5000)

    print(f"Resampled Training Set Size: {len(X_train_resampled):,} records.")
    print("Resampled Training Class Distribution:")
    print(pd.Series(y_train_resampled).value_counts().to_string())

    # 5. Save Parquet Datasets
    print("Saving processed train/val/test Parquet files...")
    train_df = pd.DataFrame(X_train_resampled, columns=FEATURE_KEYS)
    train_df["label"] = y_train_resampled

    val_df = pd.DataFrame(X_val_scaled, columns=FEATURE_KEYS)
    val_df["label"] = y_val.values

    test_df = pd.DataFrame(X_test_scaled, columns=FEATURE_KEYS)
    test_df["label"] = y_test.values

    train_df.to_parquet(PROCESSED_DIR / "train.parquet", index=False)
    val_df.to_parquet(PROCESSED_DIR / "val.parquet", index=False)
    test_df.to_parquet(PROCESSED_DIR / "test.parquet", index=False)

    print("\n================ PREPROCESSING & SPLIT SUMMARY ================")
    print(f"Train Parquet: {PROCESSED_DIR / 'train.parquet'} ({len(train_df):,} records)")
    print(f"Val Parquet:   {PROCESSED_DIR / 'val.parquet'} ({len(val_df):,} records)")
    print(f"Test Parquet:  {PROCESSED_DIR / 'test.parquet'} ({len(test_df):,} records)")
    print("==================================================================")


if __name__ == "__main__":
    preprocess_and_split()
