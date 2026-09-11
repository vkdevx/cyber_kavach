import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ValidatedPacket:
    """Represents a validated packet header metadata record (payload discarded)."""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packet_length: int
    timestamp: float
    tcp_flags: Optional[str] = None


@dataclass
class FlowRecord:
    """Represents an aggregated unidirectional network flow window."""
    flow_id: str
    correlation_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packet_count: int
    byte_count: int
    start_ts: float
    end_ts: float
    source: str = "live"
    packets: List[ValidatedPacket] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.001, self.end_ts - self.start_ts)
