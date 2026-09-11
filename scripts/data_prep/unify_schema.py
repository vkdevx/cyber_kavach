import os
import glob
import re
import numpy as np
import pandas as pd
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PARQUET = PROCESSED_DATA_DIR / "unified_dataset.parquet"

# Label Taxonomy Mapping
LABEL_TAXONOMY_MAP = {
    # Benign
    "benign": "benign",
    "normal": "benign",
    
    # Port Scan
    "portscan": "portscan",
    "portsweep": "probe",
    "satan": "probe",
    "ipsweep": "probe",
    "nmap": "probe",
    
    # DoS / DDoS
    "dos": "dos",
    "ddos": "dos",
    "dos hulk": "dos",
    "dos slowloris": "dos",
    "dos slowhttptest": "dos",
    "dos goldeneye": "dos",
    "heartbleed": "dos",
    "neptune": "dos",
    "smurf": "dos",
    "back": "dos",
    "teardrop": "dos",
    "pod": "dos",
    "land": "dos",
    "apache2": "dos",
    "processtable": "dos",
    "udpstorm": "dos",

    # Brute Force
    "ftp-patator": "bruteforce",
    "ssh-patator": "bruteforce",
    "guess_passwd": "bruteforce",

    # SQL Injection / Web Attacks
    "web attack – sql injection": "sqli",
    "web attack - sql injection": "sqli",
    "sql injection": "sqli",
    "web attack – brute force": "bruteforce",
    "web attack - brute force": "bruteforce",
    "web attack – xss": "sqli",
    "web attack - xss": "sqli",

    # R2L / U2R / Probe / Infiltration
    "infiltration": "probe",
    "bot": "probe",
    "warezclient": "r2l",
    "warezmaster": "r2l",
    "ftp_write": "r2l",
    "multihop": "r2l",
    "phf": "r2l",
    "spy": "r2l",
    "imap": "r2l",
    "buffer_overflow": "u2r",
    "loadmodule": "u2r",
    "rootkit": "u2r",
    "perl": "u2r"
}


def clean_label(label_str: str) -> str:
    """Normalizes raw label strings into unified taxonomy."""
    if not isinstance(label_str, str):
        return "benign"
    cleaned = label_str.strip().lower()
    # Remove trailing dots if present (e.g. nsl-kdd)
    cleaned = cleaned.rstrip(".")
    return LABEL_TAXONOMY_MAP.get(cleaned, "probe" if "scan" in cleaned or "bot" in cleaned else "dos" if "dos" in cleaned else "benign")


def load_cicids2017(raw_dir: Path) -> pd.DataFrame:
    """Loads and transforms CICIDS2017 CSV files into 13-feature schema."""
    cicid_dir = raw_dir / "cicid_2017"
    if not cicid_dir.exists():
        print(f"Directory {cicid_dir} not found.")
        return pd.DataFrame()

    csv_files = glob.glob(str(cicid_dir / "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {cicid_dir}.")
        return pd.DataFrame()

    frames = []
    print(f"Processing {len(csv_files)} CICIDS2017 CSV files...")

    for fpath in csv_files:
        try:
            # Read sample or chunk to prevent OOM
            df = pd.read_csv(fpath, low_memory=False, nrows=50000)
            # Strip column names
            df.columns = [c.strip() for c in df.columns]

            # Standardized 13-feature mapping
            fwd_pkts = df.get("Total Fwd Packets", 1)
            bwd_pkts = df.get("Total Backward Packets", 0)
            total_pkts = fwd_pkts + bwd_pkts

            fwd_bytes = df.get("Total Length of Fwd Packets", 0)
            bwd_bytes = df.get("Total Length of Bwd Packets", 0)
            total_bytes = fwd_bytes + bwd_bytes

            avg_pkt_size = df.get("Average Packet Size", df.get("Packet Length Mean", total_bytes / np.maximum(1, total_pkts)))
            flow_duration = df.get("Flow Duration", 0) / 1e6  # convert microsec to sec

            mean_iat = df.get("Flow IAT Mean", 0) / 1e6
            iat_std = df.get("Flow IAT Std", 0) / 1e6
            iat_var = iat_std ** 2

            # Proxy feature engineering for flow metrics
            unique_dst_ip = df.get("Destination Port", 80).apply(lambda x: 1)
            unique_dst_port = df.get("Destination Port", 80).apply(lambda x: 1)

            tcp_ratio = df.get("SYN Flag Count", 0).apply(lambda x: 1.0)
            udp_ratio = df.get("SYN Flag Count", 0).apply(lambda x: 0.0)
            icmp_ratio = df.get("SYN Flag Count", 0).apply(lambda x: 0.0)
            small_large_ratio = df.get("Min Packet Length", 0) / np.maximum(1, df.get("Max Packet Length", 1))
            byte_entropy = df.get("Packet Length Variance", 0).apply(lambda x: min(8.0, float(np.log2(x + 1.0)) if x > 0 else 0.0))

            raw_labels = df.get("Label", "BENIGN")
            norm_labels = raw_labels.astype(str).apply(clean_label)

            proc_df = pd.DataFrame({
                "total_packets": total_pkts.astype(float),
                "total_bytes": total_bytes.astype(float),
                "avg_packet_size": avg_pkt_size.astype(float),
                "flow_duration": flow_duration.astype(float),
                "mean_iat": mean_iat.astype(float),
                "iat_variance": iat_var.astype(float),
                "unique_dst_ip_count": unique_dst_ip.astype(float),
                "unique_dst_port_count": unique_dst_port.astype(float),
                "tcp_ratio": tcp_ratio.astype(float),
                "udp_ratio": udp_ratio.astype(float),
                "icmp_ratio": icmp_ratio.astype(float),
                "small_large_pkt_ratio": small_large_ratio.astype(float),
                "byte_entropy": byte_entropy.astype(float),
                "label": norm_labels,
                "dataset_source": "CICIDS2017"
            })
            frames.append(proc_df)
        except Exception as exc:
            print(f"Warning: Failed processing {fpath}: {exc}")

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_nsl_kdd(raw_dir: Path) -> pd.DataFrame:
    """Loads and transforms NSL-KDD dataset into 13-feature schema."""
    kdd_dir = raw_dir / "nsl-kdd"
    csv_file = kdd_dir / "KDDTest+.csv"
    if not csv_file.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(csv_file, header=None)
        # Standard NSL-KDD column index mapping
        duration = df[0].astype(float)
        protocol = df[1].astype(str)
        src_bytes = df[4].astype(float)
        dst_bytes = df[5].astype(float)
        count = df[22].astype(float)
        raw_label = df[41].astype(str)

        total_bytes = src_bytes + dst_bytes
        total_packets = np.maximum(1.0, count)
        avg_pkt_size = total_bytes / total_packets

        tcp_ratio = protocol.apply(lambda p: 1.0 if p == "tcp" else 0.0)
        udp_ratio = protocol.apply(lambda p: 1.0 if p == "udp" else 0.0)
        icmp_ratio = protocol.apply(lambda p: 1.0 if p == "icmp" else 0.0)

        proc_df = pd.DataFrame({
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            "avg_packet_size": avg_pkt_size,
            "flow_duration": duration,
            "mean_iat": duration / total_packets,
            "iat_variance": np.zeros(len(df)),
            "unique_dst_ip_count": df[28].astype(float),  # dst_host_count
            "unique_dst_port_count": df[29].astype(float),  # dst_host_srv_count
            "tcp_ratio": tcp_ratio,
            "udp_ratio": udp_ratio,
            "icmp_ratio": icmp_ratio,
            "small_large_pkt_ratio": np.full(len(df), 0.5),
            "byte_entropy": np.full(len(df), 4.5),
            "label": raw_label.apply(clean_label),
            "dataset_source": "NSL-KDD"
        })
        return proc_df
    except Exception as exc:
        print(f"Warning: Failed processing NSL-KDD: {exc}")
        return pd.DataFrame()


def unify_all_datasets():
    """Unifies raw datasets into 13-feature schema, cleans Inf/NaN, and exports Parquet."""
    print("Starting schema unification across raw datasets...")
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    dfs = []

    # 1. Load CICIDS2017
    df_cicids = load_cicids2017(RAW_DATA_DIR)
    if not df_cicids.empty:
        dfs.append(df_cicids)

    # 2. Load NSL-KDD
    df_kdd = load_nsl_kdd(RAW_DATA_DIR)
    if not df_kdd.empty:
        dfs.append(df_kdd)

    if not dfs:
        print("No raw datasets loaded. Exiting.")
        return

    unified_df = pd.concat(dfs, ignore_index=True)

    # Clean Inf / -Inf / NaN values explicitly
    print("Cleaning Infinite and NaN values...")
    feature_cols = [
        "total_packets", "total_bytes", "avg_packet_size", "flow_duration",
        "mean_iat", "iat_variance", "unique_dst_ip_count", "unique_dst_port_count",
        "tcp_ratio", "udp_ratio", "icmp_ratio", "small_large_pkt_ratio", "byte_entropy"
    ]

    # Replace Inf with NaN
    unified_df[feature_cols] = unified_df[feature_cols].replace([np.inf, -np.inf], np.nan)

    # Impute NaNs with column median or 0.0
    for col in feature_cols:
        median_val = unified_df[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        unified_df[col] = unified_df[col].fillna(median_val)

    # Save to Parquet
    print(f"Saving unified dataset to {OUTPUT_PARQUET}...")
    unified_df.to_parquet(OUTPUT_PARQUET, index=False)

    print("\n================ DATASET UNIFICATION SUMMARY ================")
    print(f"Total Unified Records: {len(unified_df):,}")
    print("\nRecords per Dataset Source:")
    print(unified_df["dataset_source"].value_counts().to_string())

    print("\nUnified Class Taxonomy Distribution:")
    print(unified_df["label"].value_counts().to_string())
    print("=============================================================")


if __name__ == "__main__":
    unify_all_datasets()
