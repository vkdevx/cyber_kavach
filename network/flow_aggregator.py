import time
import uuid
from typing import Dict, List, Optional, Tuple
from network.flow_models import ValidatedPacket, FlowRecord
from config.settings import settings


class FlowAggregator:
    """Aggregates validated packets into windowed unidirectional FlowRecord objects."""

    def __init__(self, window_seconds: float = None):
        self.window_seconds = window_seconds or settings.FLOW_WINDOW_SECONDS
        # Key: (src_ip, dst_ip) -> FlowRecord
        self.active_flows: Dict[Tuple[str, str], FlowRecord] = {}

    def add_packet(self, packet: ValidatedPacket, source: str = "live") -> Optional[FlowRecord]:
        """
        Adds a packet to the corresponding flow aggregation window.
        Returns a completed FlowRecord if the window has elapsed.
        """
        key = (packet.src_ip, packet.dst_ip)
        completed_flow: Optional[FlowRecord] = None

        if key in self.active_flows:
            flow = self.active_flows[key]
            # Check if flow duration exceeds sliding window size
            if packet.timestamp - flow.start_ts >= self.window_seconds:
                # Close current flow window and emit it
                flow.end_ts = max(flow.end_ts, packet.timestamp)
                completed_flow = flow

                # Start new flow window for this packet
                new_correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
                new_flow_id = f"flw_{uuid.uuid4().hex[:12]}"
                self.active_flows[key] = FlowRecord(
                    flow_id=new_flow_id,
                    correlation_id=new_correlation_id,
                    src_ip=packet.src_ip,
                    dst_ip=packet.dst_ip,
                    src_port=packet.src_port,
                    dst_port=packet.dst_port,
                    protocol=packet.protocol,
                    packet_count=1,
                    byte_count=packet.packet_length,
                    start_ts=packet.timestamp,
                    end_ts=packet.timestamp,
                    source=source,
                    packets=[packet]
                )
            else:
                # Update active flow window
                flow.packet_count += 1
                flow.byte_count += packet.packet_length
                flow.end_ts = packet.timestamp
                flow.packets.append(packet)
        else:
            # Create new flow window
            correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
            flow_id = f"flw_{uuid.uuid4().hex[:12]}"
            self.active_flows[key] = FlowRecord(
                flow_id=flow_id,
                correlation_id=correlation_id,
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                src_port=packet.src_port,
                dst_port=packet.dst_port,
                protocol=packet.protocol,
                packet_count=1,
                byte_count=packet.packet_length,
                start_ts=packet.timestamp,
                end_ts=packet.timestamp,
                source=source,
                packets=[packet]
            )

        return completed_flow

    def flush_expired_flows(self, current_ts: Optional[float] = None) -> List[FlowRecord]:
        """Flushes and returns all flows whose window has expired."""
        now = current_ts or time.time()
        expired: List[FlowRecord] = []
        keys_to_remove = []

        for key, flow in self.active_flows.items():
            if now - flow.start_ts >= self.window_seconds:
                expired.append(flow)
                keys_to_remove.append(key)

        for k in keys_to_remove:
            del self.active_flows[k]

        return expired
