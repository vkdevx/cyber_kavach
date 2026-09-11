import os
import joblib
import numpy as np
from typing import Dict, Any, Tuple
from ml.model_registry import model_registry, DummySupervisedRF, DummyUnsupervisedIF
from ml.feature_extraction import FeatureExtractor

_scaler = None
_scaler_path = "models/trained/scaler.pkl"
if os.path.exists(_scaler_path):
    try:
        _scaler = joblib.load(_scaler_path)
    except Exception:
        _scaler = None


class InferenceService:
    """Thread-safe runner executing Random Forest and Isolation Forest predictions."""

    @staticmethod
    def run_inference(features_dict: Dict[str, float]) -> Tuple[str, float, float]:
        """
        Runs ML inference on a 13-feature dictionary.
        Returns: (rf_predicted_class, rf_probability, if_anomaly_score)
        """
        vec = FeatureExtractor.to_vector(features_dict)
        X_raw = np.array([vec], dtype=np.float64)

        rf = model_registry.rf_model
        if_model = model_registry.if_model

        # Determine whether to use scaled or raw input vector
        if isinstance(rf, DummySupervisedRF):
            X_rf = X_raw
        else:
            X_rf = _scaler.transform(X_raw) if _scaler is not None else X_raw

        if isinstance(if_model, DummyUnsupervisedIF):
            X_if = X_raw
        else:
            X_if = _scaler.transform(X_raw) if _scaler is not None else X_raw

        # 1. Supervised Random Forest Prediction
        rf_probs = rf.predict_proba(X_rf)[0]
        classes = getattr(rf, "classes_", ["Benign", "Port Scanning", "Network Scanning", "DDoS-like Volumetric Behavior", "Data Exfiltration", "Beaconing"])

        best_idx = int(np.argmax(rf_probs))
        rf_class = str(classes[best_idx])
        rf_prob = float(rf_probs[best_idx])

        # 2. Unsupervised Isolation Forest Prediction
        if hasattr(if_model, "decision_function") and not isinstance(if_model, DummyUnsupervisedIF):
            raw_score = float(if_model.decision_function(X_if)[0])
            # Map sklearn decision_function (positive for inliers, negative for outliers)
            if_anomaly_score = max(0.0, min(1.0, float(round(0.5 - raw_score, 2))))
        elif isinstance(if_model, DummyUnsupervisedIF):
            raw_score = float(if_model.decision_function(X_raw)[0])
            if_anomaly_score = max(0.0, min(1.0, float(round(0.5 - raw_score, 2))))
        else:
            if_anomaly_score = 0.0

        return rf_class, rf_prob, if_anomaly_score
