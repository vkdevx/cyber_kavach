from typing import List, Optional
from sqlalchemy.orm import Session
from storage.models_orm import FlowORM, FeatureORM


class FlowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_flow(
        self,
        flow_id: str,
        correlation_id: str,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: str,
        packet_count: int,
        byte_count: int,
        start_ts: float,
        end_ts: float,
        source: str
    ) -> FlowORM:
        flow = FlowORM(
            flow_id=flow_id,
            correlation_id=correlation_id,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            packet_count=packet_count,
            byte_count=byte_count,
            start_ts=start_ts,
            end_ts=end_ts,
            source=source
        )
        self.db.add(flow)
        self.db.commit()
        self.db.refresh(flow)
        return flow

    def create_features(
        self,
        flow_id: str,
        total_packets: float,
        total_bytes: float,
        avg_packet_size: float,
        flow_duration: float,
        mean_iat: float,
        iat_variance: float,
        unique_dst_ip_count: float,
        unique_dst_port_count: float,
        tcp_ratio: float,
        udp_ratio: float,
        icmp_ratio: float,
        small_large_pkt_ratio: float,
        byte_entropy: float
    ) -> FeatureORM:
        features = FeatureORM(
            flow_id=flow_id,
            total_packets=total_packets,
            total_bytes=total_bytes,
            avg_packet_size=avg_packet_size,
            flow_duration=flow_duration,
            mean_iat=mean_iat,
            iat_variance=iat_variance,
            unique_dst_ip_count=unique_dst_ip_count,
            unique_dst_port_count=unique_dst_port_count,
            tcp_ratio=tcp_ratio,
            udp_ratio=udp_ratio,
            icmp_ratio=icmp_ratio,
            small_large_pkt_ratio=small_large_pkt_ratio,
            byte_entropy=byte_entropy
        )
        self.db.add(features)
        self.db.commit()
        self.db.refresh(features)
        return features

    def get_flow_by_id(self, flow_id: str) -> Optional[FlowORM]:
        return self.db.query(FlowORM).filter(FlowORM.flow_id == flow_id).first()

    def get_recent_flows_by_source_ip(self, src_ip: str, limit: int = 50) -> List[FlowORM]:
        return (
            self.db.query(FlowORM)
            .filter(FlowORM.src_ip == src_ip)
            .order_by(FlowORM.start_ts.desc())
            .limit(limit)
            .all()
        )
