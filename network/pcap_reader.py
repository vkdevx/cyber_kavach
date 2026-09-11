import os
from typing import List, Optional
from scapy.all import rdpcap
from network.flow_models import ValidatedPacket
from network.packet_validator import PacketValidator
from network.deduplicator import PacketDeduplicator
from backend.core.logging_setup import log_security_event


class PcapReaderService:
    """Reads offline PCAP files in read-only mode and extracts validated packets."""

    @staticmethod
    def read_pcap(filepath: str) -> List[ValidatedPacket]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PCAP file not found: {filepath}")

        log_security_event(
            event_type="PCAP_READ_START",
            message=f"Parsing PCAP file '{filepath}'",
            details={"filepath": filepath}
        )

        validator = PacketValidator()
        deduplicator = PacketDeduplicator()
        packets: List[ValidatedPacket] = []

        try:
            scapy_packets = rdpcap(filepath)
            for pkt in scapy_packets:
                val = validator.validate_scapy_packet(pkt)
                if val and not deduplicator.is_duplicate(val):
                    packets.append(val)
        except Exception as exc:
            log_security_event(
                event_type="PCAP_READ_ERROR",
                message=f"Error reading PCAP '{filepath}': {str(exc)}",
                level=40
            )
            raise

        log_security_event(
            event_type="PCAP_READ_SUCCESS",
            message=f"Parsed {len(packets)} valid packets from PCAP '{filepath}'",
            details={"packet_count": len(packets)}
        )

        return packets
