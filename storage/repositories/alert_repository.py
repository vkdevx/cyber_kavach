import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from storage.models_orm import AlertORM


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(
        self,
        alert_id: str,
        correlation_id: str,
        flow_id: str,
        risk_score: int,
        severity: str,
        confidence: float,
        threat_category: str,
        explanation: str,
        top_features: List[str],
        geolocation: dict,
        created_ts: float,
        status: str = "new",
        notes: str = ""
    ) -> AlertORM:
        alert = AlertORM(
            alert_id=alert_id,
            correlation_id=correlation_id,
            flow_id=flow_id,
            risk_score=risk_score,
            severity=severity,
            confidence=confidence,
            threat_category=threat_category,
            explanation=explanation,
            top_features=json.dumps(top_features),
            geolocation=json.dumps(geolocation),
            status=status,
            notes=notes,
            created_ts=created_ts
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_alert_by_id(self, alert_id: str) -> Optional[AlertORM]:
        return self.db.query(AlertORM).filter(AlertORM.alert_id == alert_id).first()

    def update_status(self, alert_id: str, status: str) -> Optional[AlertORM]:
        alert = self.get_alert_by_id(alert_id)
        if alert:
            alert.status = status
            self.db.commit()
            self.db.refresh(alert)
        return alert

    def update_notes(self, alert_id: str, notes: str) -> Optional[AlertORM]:
        alert = self.get_alert_by_id(alert_id)
        if alert:
            alert.notes = notes
            self.db.commit()
            self.db.refresh(alert)
        return alert

    def get_recent_alerts(self, limit: int = 50) -> List[AlertORM]:
        return (
            self.db.query(AlertORM)
            .order_by(desc(AlertORM.created_ts))
            .limit(limit)
            .all()
        )

    def filter_history(
        self,
        start_date: Optional[float] = None,
        end_date: Optional[float] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Tuple[List[AlertORM], int]:
        query = self.db.query(AlertORM)
        filters = []

        if start_date is not None:
            filters.append(AlertORM.created_ts >= start_date)
        if end_date is not None:
            filters.append(AlertORM.created_ts <= end_date)
        if category:
            filters.append(AlertORM.threat_category == category)
        if severity:
            filters.append(AlertORM.severity == severity)
        if status:
            filters.append(AlertORM.status == status)

        if filters:
            query = query.filter(and_(*filters))

        total = query.count()
        offset = (page - 1) * page_size

        items = (
            query.order_by(desc(AlertORM.created_ts))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total
