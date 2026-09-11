from typing import Dict, Any, Tuple, Optional
from config.settings import settings
from backend.risk.severity_mapper import SeverityMapper
from backend.risk.confidence_engine import ConfidenceEngine
from backend.risk.explainer import ExplainerEngine


class RiskEngine:
    """Master Risk Calculation Engine combining RF, IF, Fast Path Boost, and Rule Heuristics."""

    def __init__(self):
        self.explainer = ExplainerEngine()

    def evaluate_risk(
        self,
        features_dict: Dict[str, float],
        rf_class: str,
        rf_prob: float,
        if_score: float,
        intel_ip_match: Optional[Any] = None,
        intel_cidr_match: Optional[Any] = None
    ) -> Tuple[int, str, float, str, str, list]:
        """
        Evaluates risk score (0-100), severity band, confidence, category, explanation, and top features.
        """
        unique_ports = int(features_dict.get("unique_dst_port_count", 1))
        unique_ips = int(features_dict.get("unique_dst_ip_count", 1))
        total_pkts = int(features_dict.get("total_packets", 1))
        total_bytes = int(features_dict.get("total_bytes", 0))
        avg_pkt_size = features_dict.get("avg_packet_size", 500.0)
        mean_iat = features_dict.get("mean_iat", 0.0)
        iat_var = features_dict.get("iat_variance", 0.0)
        tcp_ratio = features_dict.get("tcp_ratio", 0.0)

        # 1. Determine Threat Category via Supervised RF & Rule Heuristics
        threat_category = "Benign"

        # Rule Heuristics Priority Path
        if unique_ports >= 15:
            threat_category = "Port Scanning"
        elif unique_ips >= 10:
            threat_category = "Network Scanning"
        elif total_pkts >= 50 or (total_pkts >= 20 and avg_pkt_size < 120 and tcp_ratio >= 0.8):
            threat_category = "SYN Flood / DoS"
        elif total_bytes >= 500000:
            threat_category = "Data Exfiltration"
        elif iat_var < 0.0005 and total_pkts >= 10 and unique_ports <= 2 and total_bytes < 5000:
            threat_category = "Beaconing"
        elif rf_prob >= 0.75 and rf_class.lower() != "benign":
            threat_category = rf_class
        elif if_score >= 0.80:
            threat_category = "Unknown Anomaly"
        elif intel_ip_match or intel_cidr_match:
            threat_category = "Known Malicious Threat Intel Match"

        # 2. Risk Score Math (Fused RF + IF weights)
        w_rf = settings.WEIGHT_SUPERVISED_RF
        w_if = settings.WEIGHT_UNSUPERVISED_IF

        rf_score_comp = 0.0 if threat_category.lower() == "benign" else (rf_prob * 100.0 if rf_prob > 0.3 else 70.0)
        if_score_comp = 0.0 if threat_category.lower() == "benign" else if_score * 100.0

        base_risk = (w_rf * rf_score_comp) + (w_if * if_score_comp)

        # 3. Fast Path Reputation Boost
        intel_boost = 0
        if intel_ip_match:
            intel_boost += int(getattr(intel_ip_match, "threat_score", 80) * 0.25)
        if intel_cidr_match:
            intel_boost += int(getattr(intel_cidr_match, "threat_score", 80) * 0.25)

        raw_score = int(round(base_risk + intel_boost))
        if threat_category.lower() == "benign" and intel_boost == 0 and if_score < 0.6:
            risk_score = min(10, raw_score)
        else:
            risk_score = max(0, min(100, raw_score))

        # 4. Severity Band Mapping
        severity = SeverityMapper.map_score_to_severity(risk_score)

        # 5. Confidence Calculation
        confidence = ConfidenceEngine.calculate_confidence(rf_prob, if_score, total_pkts)

        # 6. Explanation Generation
        explanation, top_features = self.explainer.generate_explanation(
            threat_category, features_dict, rf_class, rf_prob, if_score
        )

        return risk_score, severity, confidence, threat_category, explanation, top_features


risk_engine = RiskEngine()
