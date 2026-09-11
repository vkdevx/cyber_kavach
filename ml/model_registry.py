import os
import joblib
import numpy as np
from typing import Optional, Dict, Any, Tuple
from backend.core.logging_setup import log_security_event
from config.settings import settings


class DummySupervisedRF:
    """Fallback Random Forest classifier when trained pickle file is not present."""
    classes_ = np.array(["Benign", "Port Scanning", "Network Scanning", "DDoS-like Volumetric Behavior", "Data Exfiltration", "Beaconing"])

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        # X is shape (1, 13)
        # Vector indices: 0:total_pkts, 1:total_bytes, 2:avg_size, 3:duration, 4:mean_iat, 5:iat_var, 6:dst_ips, 7:dst_ports
        total_pkts = X[0][0]
        total_bytes = X[0][1]
        mean_iat = X[0][4]
        iat_var = X[0][5]
        dst_ips = X[0][6]
        dst_ports = X[0][7]

        # Heuristic probabilities mapping
        if dst_ports >= 15:
            # Port Scanning
            return np.array([[0.05, 0.85, 0.05, 0.02, 0.01, 0.02]])
        elif dst_ips >= 10:
            # Network Scanning
            return np.array([[0.05, 0.05, 0.85, 0.02, 0.01, 0.02]])
        elif total_pkts >= 200 or (mean_iat < 0.005 and total_pkts > 50):
            # DDoS Flood
            return np.array([[0.02, 0.02, 0.02, 0.90, 0.02, 0.02]])
        elif total_bytes >= 500000:
            # Data Exfiltration
            return np.array([[0.05, 0.02, 0.02, 0.02, 0.85, 0.04]])
        elif iat_var < 0.0005 and total_pkts >= 5:
            # Beaconing
            return np.array([[0.05, 0.02, 0.02, 0.02, 0.04, 0.85]])
        else:
            # Benign
            return np.array([[0.95, 0.01, 0.01, 0.01, 0.01, 0.01]])


class DummyUnsupervisedIF:
    """Fallback Isolation Forest anomaly detector when trained pickle file is not present."""

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        total_pkts = X[0][0]
        total_bytes = X[0][1]
        dst_ports = X[0][7]
        iat_var = X[0][5]

        # Return anomaly score where lower/more negative means more anomalous in sklearn
        if dst_ports >= 15 or total_pkts >= 200 or total_bytes >= 500000 or (iat_var < 0.0005 and total_pkts >= 5):
            return np.array([-0.35])  # High anomaly
        return np.array([0.25])      # Normal baseline


class ModelRegistry:
    """Manages loading and querying ML model artifacts."""

    def __init__(self):
        self.rf_model = None
        self.if_model = None
        self.degraded = False
        self.rf_version = "v1.0 (Embedded)"
        self.if_version = "v1.0 (Embedded)"
        self.load_models()

    def load_models(self):
        rf_paths = [
            "models/trained/threat_classifier_final.pkl",
            "models/threat_classifier_final.pkl",
            "models/trained/random_forest_v1.pkl",
            "models/rf_v1.pkl"
        ]
        rf_loaded = False
        for p in rf_paths:
            if os.path.exists(p):
                try:
                    self.rf_model = joblib.load(p)
                    self.rf_version = f"v2.0 ({os.path.basename(p)})"
                    log_security_event("MODEL_LOAD_SUCCESS", f"Loaded Supervised RF model from {p}")
                    rf_loaded = True
                    break
                except Exception as exc:
                    log_security_event("MODEL_LOAD_ERROR", f"Error loading RF model from {p}: {exc}", level=30)
        
        if not rf_loaded:
            self.rf_model = DummySupervisedRF()

        if_paths = [
            "models/trained/isolation_forest_v1.pkl",
            "models/if_v1.pkl"
        ]
        if_loaded = False
        for p in if_paths:
            if os.path.exists(p):
                try:
                    self.if_model = joblib.load(p)
                    self.if_version = f"v1.0 ({os.path.basename(p)})"
                    log_security_event("MODEL_LOAD_SUCCESS", f"Loaded Unsupervised IF model from {p}")
                    if_loaded = True
                    break
                except Exception as exc:
                    log_security_event("MODEL_LOAD_ERROR", f"Error loading IF model from {p}: {exc}", level=30)
        
        if not if_loaded:
            self.if_model = DummyUnsupervisedIF()


model_registry = ModelRegistry()
