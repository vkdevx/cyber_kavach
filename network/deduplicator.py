import time
from typing import Dict, Tuple
from network.flow_models import ValidatedPacket


class PacketDeduplicator:
    """Deduplicates duplicate/replayed packet sequences within a short time window."""

    def __init__(self, dedup_window_seconds: float = 1.0):
        self.dedup_window = dedup_window_seconds
        self.seen_packets: Dict[Tuple[str, str, int, int, str, int, float], float] = {}

    def is_duplicate(self, packet: ValidatedPacket) -> bool:
        now = packet.timestamp
        # Round timestamp to 2 decimal places to catch rapid duplicate replays
        key = (
            packet.src_ip,
            packet.dst_ip,
            packet.src_port,
            packet.dst_port,
            packet.protocol,
            packet.packet_length,
            round(packet.timestamp, 2)
        )

        # Cleanup expired cache entries
        expired_keys = [k for k, ts in self.seen_packets.items() if now - ts > self.dedup_window]
        for k in expired_keys:
            del self.seen_packets[k]

        if key in self.seen_packets:
            return True

        self.seen_packets[key] = now
        return False
