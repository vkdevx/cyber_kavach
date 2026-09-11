import time
from typing import Dict, Any, List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from network.packet_validator import PacketValidator
from backend.pipeline.orchestrator import orchestrator
from backend.api.deps import get_current_user, CurrentUser

router = APIRouter(tags=["Telemetry Ingestion"])


class PacketTelemetryInput(BaseModel):
    src_ip: str
    dst_ip: str
    src_port: int = 54321
    dst_port: int = 80
    protocol: str = "TCP"
    packet_length: int = 64
    timestamp: float = Field(default_factory=time.time)
    tcp_flags: str = "S"


@router.post("/api/v1/telemetry/packet", status_code=status.HTTP_202_ACCEPTED)
@router.post("/api/telemetry/packet", status_code=status.HTTP_202_ACCEPTED)
def ingest_packet(
    payload: Union[PacketTelemetryInput, List[PacketTelemetryInput]],
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Ingestion REST API endpoint for manual packet telemetry push.
    Validates packet header metadata, aggregates flows, runs hybrid AI detection, and stores alerts.
    """
    inputs = payload if isinstance(payload, list) else [payload]
    MAX_BATCH_SIZE = 500
    if len(inputs) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "BATCH_TOO_LARGE", "message": f"Maximum telemetry push batch size is {MAX_BATCH_SIZE} packets."}
        )

    processed_count = 0
    alerts_generated = []

    for item in inputs:
        val = PacketValidator.validate_dict(item.model_dump())
        if val:
            alert = orchestrator.process_packet(val, source="live")
            processed_count += 1
            if alert:
                alerts_generated.append(alert["payload"])

    # Flush active flow windows to ensure immediate processing during API push
    expired = orchestrator.aggregator.flush_expired_flows(current_ts=time.time() + 10.0)
    for flow in expired:
        alert = orchestrator.process_flow(flow)
        if alert:
            alerts_generated.append(alert["payload"])

    return {
        "status": "success",
        "processed_packets": processed_count,
        "alerts_generated_count": len(alerts_generated),
        "alerts": alerts_generated
    }
