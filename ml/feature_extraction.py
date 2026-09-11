import math
import numpy as np
from typing import Dict, List, Any
from network.flow_models import FlowRecord, ValidatedPacket


class FeatureExtractor:
    """Extracts the 13 numerical metadata features from a FlowRecord."""

    @staticmethod
    def calculate_shannon_entropy(lengths: List[int]) -> float:
        """Calculates Shannon entropy of packet byte lengths across the flow."""
        if not lengths:
            return 0.0
        counts: Dict[int, int] = {}
        for l in lengths:
            counts[l] = counts.get(l, 0) + 1
        total = len(lengths)
        entropy = 0.0
        for cnt in counts.values():
            p = cnt / total
            entropy -= p * math.log2(p)
        return float(round(entropy, 4))

    @classmethod
    def extract_features(cls, flow: FlowRecord) -> Dict[str, float]:
        packets = flow.packets
        total_packets = float(flow.packet_count)
        total_bytes = float(flow.byte_count)
        flow_duration = max(0.001, flow.duration)

        avg_packet_size = total_bytes / total_packets if total_packets > 0 else 0.0

        # Inter-arrival times (IAT)
        iats: List[float] = []
        if len(packets) > 1:
            # Sort packets by timestamp just in case
            sorted_pkts = sorted(packets, key=lambda p: p.timestamp)
            for i in range(1, len(sorted_pkts)):
                dt = sorted_pkts[i].timestamp - sorted_pkts[i-1].timestamp
                iats.append(max(0.0, dt))

        if iats:
            mean_iat = float(np.mean(iats))
            iat_variance = float(np.var(iats))
        else:
            mean_iat = flow_duration
            iat_variance = 0.0

        # Unique destination count
        unique_dst_ips = len(set(p.dst_ip for p in packets)) if packets else 1
        unique_dst_ports = len(set(p.dst_port for p in packets)) if packets else 1

        # Protocol distribution
        tcp_cnt = sum(1 for p in packets if p.protocol == "TCP") if packets else (1 if flow.protocol == "TCP" else 0)
        udp_cnt = sum(1 for p in packets if p.protocol == "UDP") if packets else (1 if flow.protocol == "UDP" else 0)
        icmp_cnt = sum(1 for p in packets if p.protocol == "ICMP") if packets else (1 if flow.protocol == "ICMP" else 0)

        tcp_ratio = tcp_cnt / total_packets if total_packets > 0 else 0.0
        udp_ratio = udp_cnt / total_packets if total_packets > 0 else 0.0
        icmp_ratio = icmp_cnt / total_packets if total_packets > 0 else 0.0

        # Small (<128B) vs Large (>1024B) packet ratio
        small_pkts = sum(1 for p in packets if p.packet_length < 128) if packets else 0
        large_pkts = sum(1 for p in packets if p.packet_length > 1024) if packets else 0
        small_large_ratio = small_pkts / max(1, large_pkts)

        # Byte entropy
        lengths = [p.packet_length for p in packets] if packets else [int(avg_packet_size)]
        byte_entropy = cls.calculate_shannon_entropy(lengths)

        return {
            "total_packets": float(round(total_packets, 2)),
            "total_bytes": float(round(total_bytes, 2)),
            "avg_packet_size": float(round(avg_packet_size, 2)),
            "flow_duration": float(round(flow_duration, 4)),
            "mean_iat": float(round(mean_iat, 6)),
            "iat_variance": float(round(iat_variance, 6)),
            "unique_dst_ip_count": float(unique_dst_ips),
            "unique_dst_port_count": float(unique_dst_ports),
            "tcp_ratio": float(round(tcp_ratio, 4)),
            "udp_ratio": float(round(udp_ratio, 4)),
            "icmp_ratio": float(round(icmp_ratio, 4)),
            "small_large_pkt_ratio": float(round(small_large_ratio, 4)),
            "byte_entropy": float(round(byte_entropy, 4))
        }

    @classmethod
    def to_vector(cls, features_dict: Dict[str, float]) -> List[float]:
        """Converts feature dictionary to exact 13-element ordered list for ML models."""
        keys = [
            "total_packets", "total_bytes", "avg_packet_size", "flow_duration",
            "mean_iat", "iat_variance", "unique_dst_ip_count", "unique_dst_port_count",
            "tcp_ratio", "udp_ratio", "icmp_ratio", "small_large_pkt_ratio", "byte_entropy"
        ]
        return [features_dict.get(k, 0.0) for k in keys]
