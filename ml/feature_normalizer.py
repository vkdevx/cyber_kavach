from typing import Dict, List


class FeatureNormalizer:
    """Normalizes raw 13-feature vector against learned baseline bounds."""

    def __init__(self):
        # Learned benign baseline means and standard deviations
        self.baselines = {
            "total_packets": {"mean": 25.0, "std": 15.0},
            "total_bytes": {"mean": 15000.0, "std": 10000.0},
            "avg_packet_size": {"mean": 500.0, "std": 300.0},
            "flow_duration": {"mean": 3.0, "std": 1.5},
            "mean_iat": {"mean": 0.1, "std": 0.08},
            "iat_variance": {"mean": 0.05, "std": 0.04},
            "unique_dst_ip_count": {"mean": 1.2, "std": 0.5},
            "unique_dst_port_count": {"mean": 1.5, "std": 0.8},
            "tcp_ratio": {"mean": 0.8, "std": 0.3},
            "udp_ratio": {"mean": 0.15, "std": 0.2},
            "icmp_ratio": {"mean": 0.05, "std": 0.1},
            "small_large_pkt_ratio": {"mean": 0.3, "std": 0.2},
            "byte_entropy": {"mean": 4.5, "std": 1.2}
        }

    def compute_z_scores(self, features_dict: Dict[str, float]) -> Dict[str, float]:
        """Calculates Z-scores relative to baseline for XAI explanation generator."""
        z_scores = {}
        for feature_name, val in features_dict.items():
            b = self.baselines.get(feature_name, {"mean": 1.0, "std": 1.0})
            mean = b["mean"]
            std = max(0.001, b["std"])
            z_scores[feature_name] = round((val - mean) / std, 2)
        return z_scores
