import time
import uuid
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from config.settings import settings
from storage.db import SessionLocal
from storage.repositories.flow_repository import FlowRepository
from storage.repositories.alert_repository import AlertRepository
from storage.repositories.model_result_repository import ModelResultRepository
from storage.repositories.threat_intel_repository import ThreatIntelRepository

from network.flow_models import ValidatedPacket, FlowRecord
from network.flow_aggregator import FlowAggregator
from ml.feature_extraction import FeatureExtractor
from ml.inference_service import InferenceService
from backend.risk.risk_engine import risk_engine
from backend.api.ws_manager import ws_manager
from backend.core.logging_setup import log_security_event


class PipelineOrchestrator:
    """Master linear pipeline orchestrator running ingestion -> extraction -> detection -> persistence -> WS stream."""

    def __init__(self):
        self.aggregator = FlowAggregator()

    def process_packet(self, packet: ValidatedPacket, source: str = "live") -> Optional[Dict[str, Any]]:
        """Processes an incoming validated packet. Returns alert event payload if an alert is generated."""
        completed_flow = self.aggregator.add_packet(packet, source=source)
        if completed_flow:
            return self.process_flow(completed_flow)
        return None

    def process_flow(self, flow: FlowRecord) -> Optional[Dict[str, Any]]:
        """
        Executes feature extraction, threat intel lookup, ML inference, risk scoring, DB persistence, and alert dispatch for a flow.
        """
        db: Session = SessionLocal()
        try:
            flow_repo = FlowRepository(db)
            alert_repo = AlertRepository(db)
            model_res_repo = ModelResultRepository(db)
            intel_repo = ThreatIntelRepository(db)

            # 1. Persist Flow Record
            flow_orm = flow_repo.create_flow(
                flow_id=flow.flow_id,
                correlation_id=flow.correlation_id,
                src_ip=flow.src_ip,
                dst_ip=flow.dst_ip,
                src_port=flow.src_port,
                dst_port=flow.dst_port,
                protocol=flow.protocol,
                packet_count=flow.packet_count,
                byte_count=flow.byte_count,
                start_ts=flow.start_ts,
                end_ts=flow.end_ts,
                source=flow.source
            )

            # 2. Extract 13 Numerical Features
            features_dict = FeatureExtractor.extract_features(flow)
            features_orm = flow_repo.create_features(
                flow_id=flow.flow_id,
                **features_dict
            )

            # 3. Fast Path: Threat Intel Reputation & CIDR Lookup
            intel_ip_match = intel_repo.lookup_ip(flow.src_ip)
            intel_cidr_match = intel_repo.lookup_cidr(flow.src_ip)

            # 4. AI Path: ML Inference
            rf_class, rf_prob, if_score = InferenceService.run_inference(features_dict)
            result_id = f"res_{uuid.uuid4().hex[:12]}"
            model_res_repo.create_result(
                result_id=result_id,
                flow_id=flow.flow_id,
                rf_class=rf_class,
                rf_probability=rf_prob,
                if_anomaly_score=if_score,
                model_version="v1.0",
                inference_ts=time.time()
            )

            # 5. Risk Engine & Fusion
            risk_score, severity, confidence, threat_category, explanation, top_features = (
                risk_engine.evaluate_risk(
                    features_dict=features_dict,
                    rf_class=rf_class,
                    rf_prob=rf_prob,
                    if_score=if_score,
                    intel_ip_match=intel_ip_match,
                    intel_cidr_match=intel_cidr_match
                )
            )

            # 6. Generate Alert if Risk Score >= Threshold
            alert_payload = None
            if risk_score >= settings.ALERT_THRESHOLD or threat_category != "Benign":
                alert_id = f"alt_{uuid.uuid4().hex[:12]}"
                geolocation = {
                    "country": getattr(intel_ip_match, "country_code", "Germany") if intel_ip_match else "Unknown",
                    "city": "Frankfurt" if intel_ip_match else "Unknown",
                    "is_approximate": True
                }

                alert_orm = alert_repo.create_alert(
                    alert_id=alert_id,
                    correlation_id=flow.correlation_id,
                    flow_id=flow.flow_id,
                    risk_score=risk_score,
                    severity=severity,
                    confidence=confidence,
                    threat_category=threat_category,
                    explanation=explanation,
                    top_features=top_features,
                    geolocation=geolocation,
                    created_ts=time.time()
                )

                log_security_event(
                    event_type="THREAT_ALERT_GENERATED",
                    message=f"Alert generated for flow {flow.flow_id}: {threat_category} (Score: {risk_score}, Severity: {severity})",
                    src_ip=flow.src_ip,
                    correlation_id=flow.correlation_id,
                    details={"alert_id": alert_id, "risk_score": risk_score, "severity": severity}
                )

                # Prepare alert payload for WebSocket stream
                alert_payload = {
                    "event_type": "ALERT_NEW",
                    "payload": {
                        "alert_id": alert_id,
                        "correlation_id": flow.correlation_id,
                        "flow_id": flow.flow_id,
                        "src_ip": flow.src_ip,
                        "dst_ip": flow.dst_ip,
                        "src_port": flow.src_port,
                        "dst_port": flow.dst_port,
                        "protocol": flow.protocol,
                        "risk_score": risk_score,
                        "severity": severity,
                        "confidence": confidence,
                        "threat_category": threat_category,
                        "explanation": explanation,
                        "top_features": top_features,
                        "geolocation": geolocation,
                        "timestamp": time.time()
                    }
                }

                # Try broadcasting to active WebSocket connections if asyncio loop is running
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(ws_manager.broadcast(alert_payload))
                except RuntimeError:
                    pass

            return alert_payload

        finally:
            db.close()


orchestrator = PipelineOrchestrator()
