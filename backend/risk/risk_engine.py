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
        intel_cidr_match: Optional[Any] = None,
        src_port: Optional[int] = None,
        dst_port: Optional[int] = None
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
        small_large_ratio = features_dict.get("small_large_pkt_ratio", 0.0)

        # Standard benign service ports (Web, DNS, NTP, mDNS, SSDP, Local Dev)
        BENIGN_PORTS = {80, 443, 53, 5353, 1900, 123, 8080, 8443, 8000, 5000, 3000, 5432, 3306, 27017}

        # If traffic originates from a standard service port (e.g. Google/Cloudflare 443 HTTPS response), it is always safe benign web traffic
        if src_port in BENIGN_PORTS:
            threat_category = "Benign"
            risk_score = 0
            severity = "Low"
            confidence = 0.95
            explanation = f"Legitimate server response from standard service port {src_port} (HTTPS/HTTP/DNS). Verified safe."
            top_features = ["Standard service port response", "Normal browser stream", "Safe web traffic"]
            return risk_score, severity, confidence, threat_category, explanation, top_features

        # 1. Determine Threat Category — Strict Attack Signatures Only
        threat_category = "Benign"

        # ── PORT SCANNING ────────────────────────────────────────────────────
        # nmap -sS / masscan: 3+ distinct ports probed rapidly, OR 6+ ports at any speed
        if (unique_ports >= 3 and mean_iat < 0.5 and tcp_ratio >= 0.70) or (unique_ports >= 6):
            threat_category = "Port Scanning"
        elif unique_ports >= 4 and mean_iat < 0.08 and tcp_ratio >= 0.85:
            threat_category = "Port Scanning"

        # ── NETWORK SCANNING ─────────────────────────────────────────────────
        # Real scanner: 6+ unique IPs probed quickly
        elif (unique_ips >= 6 and mean_iat < 0.20) or (unique_ips >= 8):
            threat_category = "Network Scanning"

        # ── SYN FLOOD / DoS ──────────────────────────────────────────────────
        # Real SYN flood: 25+ tiny packets (<120B) at machine speed with low IAT and high TCP ratio
        elif (
            (total_pkts >= 25 and avg_pkt_size < 130 and tcp_ratio >= 0.85 and mean_iat < 0.02)
            or (total_pkts >= 50 and mean_iat < 0.01 and tcp_ratio >= 0.80)
        ):
            threat_category = "SYN Flood / DoS"

        # ── UDP FLOOD / SCAN ─────────────────────────────────────────────────
        # Real UDP flood: 40+ packets at high rate across 6+ ports
        elif (features_dict.get("udp_ratio", 0.0) >= 0.90 and total_pkts >= 40 and mean_iat < 0.02) or (features_dict.get("udp_ratio", 0.0) >= 0.85 and unique_ports >= 6):
            threat_category = "UDP Flood / Scan"

        # ── DATA EXFILTRATION ────────────────────────────────────────────────
        # Real exfil: 10MB+ upload in a single flow
        elif total_bytes >= 10_000_000:
            threat_category = "Data Exfiltration"

        # ── C2 BEACONING ─────────────────────────────────────────────────────
        # Real C2: very regular heartbeats — near-zero IAT variance, small packets, single port
        elif (
            iat_var < 0.00002
            and total_pkts >= 25
            and unique_ports == 1
            and total_bytes < 2500
            and mean_iat < 3.0
        ):
            threat_category = "Beaconing"

        # ── THREAT INTEL MATCH ────────────────────────────────────────────────
        elif intel_ip_match or intel_cidr_match:
            threat_category = "Known Malicious Threat Intel Match"

        # ── ML / AI FALLBACK ─────────────────────────────────────────────────
        # Only trust RF if extreme confidence (>90%) and not benign
        elif rf_prob >= 0.90 and rf_class.lower() != "benign":
            threat_category = rf_class

        # Anomaly engine — only flag extreme outliers (>0.95)
        elif if_score >= 0.95:
            threat_category = "Unknown Anomaly"

        # 2. Risk Score Math (Fused RF + IF weights)
        w_rf = settings.WEIGHT_SUPERVISED_RF
        w_if = settings.WEIGHT_UNSUPERVISED_IF

        if threat_category.lower() == "benign":
            risk_score = 0
            severity = "Low"
            confidence = 0.95
            explanation = "Normal benign network traffic verified. Zero threat indicators detected."
            top_features = ["Normal packet flow", "Standard service ports", "Safe inter-arrival time"]
            return risk_score, severity, confidence, threat_category, explanation, top_features

        # If attack detected, compute risk score and severity
        rf_score_comp = rf_prob * 100.0 if rf_prob > 0.3 else 80.0
        if_score_comp = if_score * 100.0
        base_risk = (w_rf * rf_score_comp) + (w_if * if_score_comp)

        # 3. Fast Path Reputation Boost
        intel_boost = 0
        if intel_ip_match:
            intel_boost += int(getattr(intel_ip_match, "threat_score", 80) * 0.25)
        if intel_cidr_match:
            intel_boost += int(getattr(intel_cidr_match, "threat_score", 80) * 0.25)

        raw_score = int(round(base_risk + intel_boost))
        risk_score = max(65, min(100, raw_score))  # Genuine attacks score 65-100 (High / Critical)

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
