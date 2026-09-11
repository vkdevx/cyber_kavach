from typing import List, Optional
from sqlalchemy.orm import Session
from storage.models_orm import ThreatIntelIPORM, ThreatIntelCIDRORM


class ThreatIntelRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_ip(
        self,
        ip: str,
        threat_score: int,
        category: str,
        source_feed: str,
        country_code: str,
        last_seen: float
    ) -> ThreatIntelIPORM:
        record = self.db.query(ThreatIntelIPORM).filter(ThreatIntelIPORM.ip == ip).first()
        if record:
            record.threat_score = threat_score
            record.category = category
            record.source_feed = source_feed
            record.country_code = country_code
            record.last_seen = last_seen
        else:
            record = ThreatIntelIPORM(
                ip=ip,
                threat_score=threat_score,
                category=category,
                source_feed=source_feed,
                country_code=country_code,
                last_seen=last_seen
            )
            self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def upsert_cidr(
        self,
        cidr_id: str,
        cidr_block: str,
        threat_score: int,
        category: str,
        source_feed: str,
        created_ts: float
    ) -> ThreatIntelCIDRORM:
        record = self.db.query(ThreatIntelCIDRORM).filter(ThreatIntelCIDRORM.cidr_block == cidr_block).first()
        if record:
            record.threat_score = threat_score
            record.category = category
            record.source_feed = source_feed
        else:
            record = ThreatIntelCIDRORM(
                cidr_id=cidr_id,
                cidr_block=cidr_block,
                threat_score=threat_score,
                category=category,
                source_feed=source_feed,
                created_ts=created_ts
            )
            self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def lookup_ip(self, ip: str) -> Optional[ThreatIntelIPORM]:
        return self.db.query(ThreatIntelIPORM).filter(ThreatIntelIPORM.ip == ip).first()

    def get_all_cidrs(self) -> List[ThreatIntelCIDRORM]:
        return self.db.query(ThreatIntelCIDRORM).all()

    def lookup_cidr(self, ip: str) -> Optional[ThreatIntelCIDRORM]:
        """Checks if an IP falls within any registered malicious CIDR blocks."""
        try:
            import ipaddress
            target_ip = ipaddress.ip_address(ip)
            cidrs = self.get_all_cidrs()
            for c in cidrs:
                if target_ip in ipaddress.ip_network(c.cidr_block, strict=False):
                    return c
        except Exception:
            pass
        return None
