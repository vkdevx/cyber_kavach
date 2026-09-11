import time
import ipaddress
from typing import Optional, Dict, Any
from network.flow_models import ValidatedPacket
from backend.core.logging_setup import log_security_event


class PacketValidator:
    """Validates raw packet header metadata and discards packet payload bytes."""

    @staticmethod
    def _is_valid_ip(ip_str: str) -> bool:
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_dict(packet_dict: Dict[str, Any]) -> Optional[ValidatedPacket]:
        """Validates packet metadata dict (e.g. from JSON telemetry push)."""
        try:
            src_ip = str(packet_dict.get("src_ip", "")).strip()
            dst_ip = str(packet_dict.get("dst_ip", "")).strip()
            if not src_ip or not dst_ip or not PacketValidator._is_valid_ip(src_ip) or not PacketValidator._is_valid_ip(dst_ip):
                return None

            src_port = int(packet_dict.get("src_port", 0))
            dst_port = int(packet_dict.get("dst_port", 0))
            if not (0 <= src_port <= 65535) or not (0 <= dst_port <= 65535):
                return None

            protocol = str(packet_dict.get("protocol", "TCP")).upper()[:10]
            packet_length = max(1, min(65535, int(packet_dict.get("packet_length", 64))))
            timestamp = float(packet_dict.get("timestamp", time.time()))
            tcp_flags = str(packet_dict.get("tcp_flags"))[:10] if packet_dict.get("tcp_flags") else None

            return ValidatedPacket(
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                packet_length=packet_length,
                timestamp=timestamp,
                tcp_flags=tcp_flags
            )
        except Exception as exc:
            log_security_event(
                event_type="MALFORMED_PACKET_DROPPED",
                message=f"Packet validation error: {str(exc)}",
                level=20
            )
            return None

    @staticmethod
    def validate_scapy_packet(pkt: Any) -> Optional[ValidatedPacket]:
        """Extracts header metadata from a Scapy packet object and discards payload."""
        try:
            # Check for IP layer
            if not pkt.haslayer("IP"):
                return None

            ip_layer = pkt["IP"]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            packet_length = len(pkt)
            timestamp = float(getattr(pkt, "time", time.time()))

            src_port = 0
            dst_port = 0
            protocol = "IP"
            tcp_flags = None

            if pkt.haslayer("TCP"):
                tcp = pkt["TCP"]
                src_port = tcp.sport
                dst_port = tcp.dport
                protocol = "TCP"
                tcp_flags = str(tcp.flags)
            elif pkt.haslayer("UDP"):
                udp = pkt["UDP"]
                src_port = udp.sport
                dst_port = udp.dport
                protocol = "UDP"
            elif pkt.haslayer("ICMP"):
                protocol = "ICMP"

            return ValidatedPacket(
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                packet_length=packet_length,
                timestamp=timestamp,
                tcp_flags=tcp_flags
            )
        except Exception as exc:
            log_security_event(
                event_type="MALFORMED_SCAPY_PACKET_DROPPED",
                message=f"Scapy packet parsing error: {str(exc)}",
                level=20
            )
            return None
