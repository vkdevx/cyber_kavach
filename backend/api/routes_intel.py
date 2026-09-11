import time
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from storage.db import get_db
from storage.models_orm import ThreatIntelIPORM
from storage.repositories.threat_intel_repository import ThreatIntelRepository
from backend.api.deps import get_current_user, CurrentUser

router = APIRouter(tags=["Threat Intelligence"])


class ThreatIntelIPInput(BaseModel):
    ip: str
    threat_score: int = Field(..., ge=0, le=100)
    category: str = "scanner"
    source_feed: str = "custom_analyst"
    country_code: str = "XX"


@router.get("/api/v1/threat-intel/ips")
def list_threat_ips(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    ips = db.query(ThreatIntelIPORM).all()
    return [
        {
            "ip": item.ip,
            "threat_score": item.threat_score,
            "category": item.category,
            "source_feed": item.source_feed,
            "country_code": item.country_code,
            "last_seen": item.last_seen
        }
        for item in ips
    ]


@router.post("/api/v1/threat-intel/ips", status_code=status.HTTP_201_CREATED)
def add_threat_ip(
    req: ThreatIntelIPInput,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    repo = ThreatIntelRepository(db)
    record = repo.upsert_ip(
        ip=req.ip.strip(),
        threat_score=req.threat_score,
        category=req.category,
        source_feed=req.source_feed,
        country_code=req.country_code,
        last_seen=time.time()
    )
    return {
        "status": "success",
        "ip": record.ip,
        "threat_score": record.threat_score,
        "category": record.category,
        "source_feed": record.source_feed
    }


@router.get("/api/v1/threat-intel/ips/{ip}")
def lookup_threat_ip(
    ip: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    repo = ThreatIntelRepository(db)
    record = repo.lookup_ip(ip.strip())
    if not record:
        return {
            "ip": ip,
            "listed": False,
            "threat_score": 0,
            "category": "Clean / Unknown",
            "source_feed": "N/A"
        }

    return {
        "ip": record.ip,
        "listed": True,
        "threat_score": record.threat_score,
        "category": record.category,
        "source_feed": record.source_feed,
        "country_code": record.country_code,
        "last_seen": record.last_seen
    }


@router.get("/api/geolocation/{ip}")
def get_geolocation(
    ip: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    clean_ip = ip.strip()
    if clean_ip.startswith("192.168.") or clean_ip.startswith("10.") or clean_ip.startswith("172.16."):
        return {
            "ip": clean_ip,
            "country": "Local Network (RFC1918)",
            "state": "Internal Subnet",
            "city": "Private IP",
            "lat": 0.0,
            "lon": 0.0,
            "is_approximate": True
        }

    return {
        "ip": clean_ip,
        "country": "Germany",
        "state": "Hesse",
        "city": "Frankfurt",
        "lat": 50.1109,
        "lon": 8.6821,
        "is_approximate": True
    }
