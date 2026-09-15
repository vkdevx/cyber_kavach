from typing import Dict, List, Tuple
from ml.feature_normalizer import FeatureNormalizer


class ExplainerEngine:
    """Generates plain-language feature-importance explanations for detected threat alerts."""

    def __init__(self):
        self.normalizer = FeatureNormalizer()

    def generate_explanation(
        self,
        threat_category: str,
        features_dict: Dict[str, float],
        rf_class: str,
        rf_prob: float,
        if_score: float
    ) -> Tuple[str, List[str]]:
        z_scores = self.normalizer.compute_z_scores(features_dict)

        # Identify top contributing features by absolute Z-score deviation
        sorted_features = sorted(z_scores.items(), key=lambda item: abs(item[1]), reverse=True)
        top_features = [f[0] for f in sorted_features[:3]]

        unique_ports = int(features_dict.get("unique_dst_port_count", 1))
        unique_ips = int(features_dict.get("unique_dst_ip_count", 1))
        total_pkts = int(features_dict.get("total_packets", 1))
        total_bytes = int(features_dict.get("total_bytes", 0))
        mean_iat = features_dict.get("mean_iat", 0.0)
        iat_var = features_dict.get("iat_variance", 0.0)

        explanation = ""

        if threat_category == "Port Scanning":
            explanation = (
                f"Destination port diversity is {unique_ports}x baseline ({unique_ports} unique ports contacted in flow window); "
                f"packet rate is elevated ({total_pkts} packets)."
            )
        elif threat_category == "XMAS Port Scan":
            explanation = (
                f"Stealth Nmap XMAS scan detected (FIN+PSH+URG flags set simultaneously on probe packets); "
                f"targeting {unique_ports} port(s) to evade stateful inspection."
            )
        elif threat_category == "NULL Port Scan":
            explanation = (
                f"Stealth Nmap NULL scan detected (probe packets sent with 0 TCP flags set); "
                f"targeting {unique_ports} port(s) to elicit RST responses."
            )
        elif threat_category == "FIN Port Scan":
            explanation = (
                f"Stealth Nmap FIN scan detected (lone FIN flag sent without prior handshake); "
                f"targeting {unique_ports} port(s)."
            )
        elif threat_category in ["SYN Flood / DoS", "DDoS-like Volumetric Behavior"]:
            explanation = (
                f"SYN Flood / DoS signature detected ({total_pkts} packets at high machine rate, mean IAT: {mean_iat:.4f}s); "
                f"half-open connection pool exhaustion attempt."
            )
        elif threat_category == "Network Scanning":
            explanation = (
                f"Destination IP diversity is {unique_ips}x baseline ({unique_ips} distinct target hosts scanned in 5s); "
                f"consistent protocol distribution detected."
            )
        elif threat_category == "DDoS-like Volumetric Behavior":
            explanation = (
                f"Packet transmission rate spiked to {total_pkts} pkts/5s (mean inter-arrival time: {mean_iat:.4f}s); "
                f"volumetric flood signature exceeds baseline."
            )
        elif threat_category == "Data Exfiltration":
            explanation = (
                f"Outbound byte volume spiked to {total_bytes / 1000.0:.1f} KB in 5s; "
                f"packet size distribution skewed heavily to maximum MTU."
            )
        elif threat_category == "Beaconing":
            explanation = (
                f"Inter-arrival timing is unusually rigid (IAT variance: {iat_var:.6f}); "
                f"periodic automated pulse detected to destination endpoint."
            )
        elif threat_category == "Known Malicious Threat Intel Match":
            explanation = (
                "Source IP or destination CIDR matches historical attacking IP blacklist / C2 infrastructure."
            )
        else:
            top_desc = ", ".join(top_features)
            explanation = (
                f"Unusual statistical deviation detected by Isolation Forest (anomaly score: {if_score:.2f}). "
                f"Top anomalous features: {top_desc}."
            )

        return explanation, top_features
