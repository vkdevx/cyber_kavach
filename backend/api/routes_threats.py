import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from storage.db import get_db
from storage.repositories.alert_repository import AlertRepository
from backend.api.schemas import (
    AlertResponse, AlertHistoryResponse, AlertStatusUpdateRequest, AlertNotesUpdateRequest
)
from backend.api.deps import get_current_user, CurrentUser

router = APIRouter(tags=["Threat Alerts"])


def _format_alert_orm(alert) -> AlertResponse:
    geolocation_data = json.loads(alert.geolocation) if isinstance(alert.geolocation, str) else alert.geolocation
    top_features_data = json.loads(alert.top_features) if isinstance(alert.top_features, str) else alert.top_features

    return AlertResponse(
        alert_id=alert.alert_id,
        correlation_id=alert.correlation_id,
        flow_id=alert.flow_id,
        risk_score=alert.risk_score,
        severity=alert.severity,
        confidence=alert.confidence,
        threat_category=alert.threat_category,
        explanation=alert.explanation,
        top_features=top_features_data if isinstance(top_features_data, list) else [],
        geolocation=geolocation_data if isinstance(geolocation_data, dict) else {},
        status=alert.status,
        notes=alert.notes or "",
        created_ts=alert.created_ts
    )


@router.get("/api/v1/threats", response_model=AlertHistoryResponse)
@router.get("/api/alerts", response_model=List[AlertResponse])
def get_threats(
    severity: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    src_ip: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    repo = AlertRepository(db)
    items, total = repo.filter_history(
        category=category,
        severity=severity,
        status=status_filter,
        page=page,
        page_size=page_size
    )

    formatted = [_format_alert_orm(a) for a in items]

    # If endpoint called via /api/alerts (list format), return list
    return AlertHistoryResponse(
        items=formatted,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/api/v1/threats/{alert_id}", response_model=AlertResponse)
@router.get("/api/alerts/{alert_id}", response_model=AlertResponse)
def get_threat_detail(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    repo = AlertRepository(db)
    alert = repo.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert with ID '{alert_id}' does not exist."}
        )
    return _format_alert_orm(alert)


@router.post("/api/v1/threats/{alert_id}/ack", response_model=AlertResponse)
@router.post("/api/alerts/{alert_id}/ack", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    repo = AlertRepository(db)
    alert = repo.update_status(alert_id, "acknowledged")
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert with ID '{alert_id}' does not exist."}
        )
    return _format_alert_orm(alert)


@router.post("/api/v1/threats/{alert_id}/false-positive", response_model=AlertResponse)
@router.post("/api/alerts/{alert_id}/false-positive", response_model=AlertResponse)
def mark_false_positive(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    repo = AlertRepository(db)
    alert = repo.update_status(alert_id, "false_positive")
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert with ID '{alert_id}' does not exist."}
        )
    return _format_alert_orm(alert)


@router.post("/api/alerts/{alert_id}/notes", response_model=AlertResponse)
def update_notes(
    alert_id: str,
    req: AlertNotesUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    repo = AlertRepository(db)
    alert = repo.update_notes(alert_id, req.notes)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ALERT_NOT_FOUND", "message": f"Alert with ID '{alert_id}' does not exist."}
        )
    return _format_alert_orm(alert)
