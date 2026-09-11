import time
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from storage.db import get_db
from storage.models_orm import FlowORM, AlertORM
from backend.api.deps import get_current_user, CurrentUser

router = APIRouter(tags=["Dashboard"])


@router.get("/api/v1/dashboard/stats")
@router.get("/api/stats/live")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Returns real-time dashboard volumetric overview, active threat counts, and top attacked ports.
    Calculated directly from SQLite database records.
    """
    total_packets = db.query(func.sum(FlowORM.packet_count)).scalar() or 0
    total_flows = db.query(func.count(FlowORM.flow_id)).scalar() or 0

    total_alerts = db.query(func.count(AlertORM.alert_id)).scalar() or 0

    # Active threat level: count only NEW / UNACKNOWLEDGED alerts (not acknowledged or false_positive)
    # This ensures threat level drops back to Low once SOC acknowledges alerts
    active_critical = (
        db.query(func.count(AlertORM.alert_id))
        .filter(AlertORM.severity == "Critical")
        .filter(AlertORM.status.notin_(["acknowledged", "false_positive"]))
        .scalar() or 0
    )
    active_high = (
        db.query(func.count(AlertORM.alert_id))
        .filter(AlertORM.severity == "High")
        .filter(AlertORM.status.notin_(["acknowledged", "false_positive"]))
        .scalar() or 0
    )
    active_medium = (
        db.query(func.count(AlertORM.alert_id))
        .filter(AlertORM.severity == "Medium")
        .filter(AlertORM.status.notin_(["acknowledged", "false_positive"]))
        .scalar() or 0
    )
    active_total = (
        db.query(func.count(AlertORM.alert_id))
        .filter(AlertORM.status.notin_(["acknowledged", "false_positive"]))
        .scalar() or 0
    )

    suspicious_flows = active_total
    safe_flows = max(0, total_flows - suspicious_flows)

    if active_critical > 0:
        active_threat_level = "Critical"
    elif active_high > 0:
        active_threat_level = "High"
    elif active_medium > 0:
        active_threat_level = "Medium"
    elif active_total > 0:
        active_threat_level = "Low"
    else:
        active_threat_level = "Low"

    tcp_flows = db.query(func.count(FlowORM.flow_id)).filter(FlowORM.protocol == "TCP").scalar() or 0
    udp_flows = db.query(func.count(FlowORM.flow_id)).filter(FlowORM.protocol == "UDP").scalar() or 0
    icmp_flows = db.query(func.count(FlowORM.flow_id)).filter(FlowORM.protocol == "ICMP").scalar() or 0

    top_ports_query = (
        db.query(FlowORM.dst_port, func.count(FlowORM.dst_port).label("count"))
        .group_by(FlowORM.dst_port)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )
    top_attacked_ports = [{"port": p[0], "count": p[1]} for p in top_ports_query]

    return {
        "total_packets": int(total_packets),
        "total_flows": int(total_flows),
        "safe_flows": int(safe_flows),
        "suspicious_flows": int(suspicious_flows),
        "active_threat_level": active_threat_level,
        "protocol_breakdown": {
            "tcp": int(tcp_flows),
            "udp": int(udp_flows),
            "icmp": int(icmp_flows)
        },
        "top_attacked_ports": top_attacked_ports,
        "timestamp": time.time()
    }


@router.get("/api/v1/dashboard/threats-over-time")
@router.get("/api/dashboard/threats-over-time")
def get_threats_over_time(
    timeframe: str = Query("1h", pattern="^(1h|24h|7d|30d)$"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Returns real-time time-binned threat counts broken down by severity and threat attack category.
    - 1h: 12 bins (every 5 mins) formatted in minutes (%H:%M)
    - 24h: 12 bins (every 2 hours) formatted in hours (%H:00)
    - 7d: 7 bins (every day) formatted in days (%a %d %b)
    - 30d: 15 bins (every 2 days) formatted in dates (%d %b)
    """
    now = time.time()
    if timeframe == "1h":
        window_seconds = 3600
        num_bins = 12  # Every 5 minutes
    elif timeframe == "7d":
        window_seconds = 7 * 86400
        num_bins = 7   # Daily bins
    elif timeframe == "30d":
        window_seconds = 30 * 86400
        num_bins = 15  # Every 2 days
    else:  # 24h
        window_seconds = 86400
        num_bins = 12  # Every 2 hours

    start_ts = now - window_seconds
    bin_size = window_seconds / num_bins

    alerts = db.query(AlertORM).filter(AlertORM.created_ts >= start_ts).all()

    bins = []
    for i in range(num_bins):
        b_start = start_ts + i * bin_size
        b_end = b_start + bin_size

        b_alerts = [a for a in alerts if b_start <= a.created_ts < (b_end if i < num_bins - 1 else now + 1.0)]

        # Format using local timezone for accurate user display
        dt = datetime.fromtimestamp(b_start)
        if timeframe == "1h":
            label = dt.strftime("%H:%M")          # Minutes (e.g. 21:05, 21:10)
        elif timeframe == "24h":
            label = dt.strftime("%H:00")          # Hours (e.g. 02:00, 04:00, 06:00)
        elif timeframe == "7d":
            label = dt.strftime("%a %d %b")       # 7 Days (e.g. Mon 08 Sep)
        else:  # 30d
            label = dt.strftime("%d %b")          # 30 Days (e.g. 12 Aug, 15 Aug)

        crit = sum(1 for a in b_alerts if a.severity == "Critical")
        high = sum(1 for a in b_alerts if a.severity == "High")
        med = sum(1 for a in b_alerts if a.severity == "Medium")
        low = sum(1 for a in b_alerts if a.severity == "Low")

        port_scan = sum(1 for a in b_alerts if "port" in (a.threat_category or "").lower())
        syn_flood = sum(1 for a in b_alerts if "syn" in (a.threat_category or "").lower() or "dos" in (a.threat_category or "").lower())
        beaconing = sum(1 for a in b_alerts if "beacon" in (a.threat_category or "").lower())
        network_scan = sum(1 for a in b_alerts if "network" in (a.threat_category or "").lower())
        other = max(0, len(b_alerts) - (port_scan + syn_flood + beaconing + network_scan))

        bins.append({
            "timestamp": label,
            "total_threats": len(b_alerts),
            "critical": crit,
            "high": high,
            "medium": med,
            "low": low,
            "port_scan": port_scan,
            "syn_flood": syn_flood,
            "beaconing": beaconing,
            "network_scan": network_scan,
            "other": other
        })

    return {
        "timeframe": timeframe,
        "timepoints": bins,
        "total_in_window": len(alerts)
    }


@router.get("/api/v1/dashboard/category-breakdown")
@router.get("/api/dashboard/category-breakdown")
def get_category_breakdown(
    timeframe: str = Query("24h", pattern="^(1h|24h|7d|30d|all)$"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Returns threat category distribution derived from database AlertORM records.
    """
    now = time.time()
    query = db.query(AlertORM)

    if timeframe == "1h":
        query = query.filter(AlertORM.created_ts >= now - 3600)
    elif timeframe == "24h":
        query = query.filter(AlertORM.created_ts >= now - 86400)
    elif timeframe == "7d":
        query = query.filter(AlertORM.created_ts >= now - 7 * 86400)
    elif timeframe == "30d":
        query = query.filter(AlertORM.created_ts >= now - 30 * 86400)

    alerts = query.all()
    total = len(alerts)

    counts: Dict[str, int] = {}
    for a in alerts:
        cat = a.threat_category or "Anomaly"
        counts[cat] = counts.get(cat, 0) + 1

    result = []
    for cat, count in counts.items():
        pct = round((count / total * 100), 1) if total > 0 else 0.0
        result.append({
            "category": cat,
            "count": count,
            "percentage": pct
        })

    result.sort(key=lambda x: x["count"], reverse=True)

    return {
        "timeframe": timeframe,
        "categories": result,
        "total_threats": total
    }


@router.get("/api/v1/dashboard/attack-map")
@router.get("/api/dashboard/attack-map")
def get_attack_map(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Returns active geographical threat points from AlertORM and FlowORM.
    Falls back to a deterministic IP-seed table so every unique attacker
    IP plots at a distinct world location on the Leaflet map.
    """

    # Deterministic seed table: common RFC-5737 / doc IPs → real cities
    IP_GEO_SEEDS: Dict[str, Dict[str, Any]] = {
        "198.51.100.45":  {"country": "Germany",       "city": "Frankfurt",     "lat": 50.1109,  "lon":  8.6821},
        "198.51.100.88":  {"country": "Russia",        "city": "Moscow",        "lat": 55.7558,  "lon": 37.6176},
        "198.51.100.99":  {"country": "China",         "city": "Beijing",       "lat": 39.9042,  "lon": 116.4074},
        "203.0.113.99":   {"country": "North Korea",   "city": "Pyongyang",     "lat": 39.0392,  "lon": 125.7625},
        "203.0.113.55":   {"country": "Iran",          "city": "Tehran",        "lat": 35.6892,  "lon":  51.3890},
        "45.33.32.156":   {"country": "United States", "city": "New York",      "lat": 40.7128,  "lon": -74.0060},
        "185.220.101.5":  {"country": "Romania",       "city": "Bucharest",     "lat": 44.4268,  "lon":  26.1025},
        "192.168.1.105":  {"country": "India",         "city": "Mumbai",        "lat": 19.0760,  "lon":  72.8777},
        "192.168.1.200":  {"country": "Brazil",        "city": "São Paulo",     "lat": -23.5505, "lon": -46.6333},
        "10.0.0.1":       {"country": "United Kingdom","city": "London",        "lat": 51.5074,  "lon":  -0.1278},
    }

    def _geo_for_ip(ip: str, stored_geo: Dict[str, Any]) -> Dict[str, Any]:
        """Return geo dict: prefer DB value, then seed table, then hash spread."""
        # If DB has a real lat/lon (not 0/null), use it
        if stored_geo.get("lat") and stored_geo.get("lon"):
            try:
                lat = float(stored_geo["lat"])
                lon = float(stored_geo["lon"])
                if not (lat == 0.0 and lon == 0.0):
                    return stored_geo
            except (TypeError, ValueError):
                pass

        # Known-IP seed table
        if ip in IP_GEO_SEEDS:
            return IP_GEO_SEEDS[ip]

        # Deterministic hash-spread for any other IP
        import hashlib
        h = int(hashlib.md5(ip.encode()).hexdigest(), 16)
        lat = ((h % 1800) - 900) / 10.0      # –90 … +90
        lon = ((h // 1800 % 3600) - 1800) / 10.0  # –180 … +180
        return {"country": "Unknown", "city": ip, "lat": lat, "lon": lon}

    alerts = db.query(AlertORM).order_by(desc(AlertORM.created_ts)).limit(200).all()

    points_map: Dict[str, Dict[str, Any]] = {}
    for a in alerts:
        flow = db.query(FlowORM).filter(FlowORM.flow_id == a.flow_id).first()
        src_ip = flow.src_ip if flow else "198.51.100.45"

        # Skip private/loopback IPs — they won't appear on a world map meaningfully
        if src_ip.startswith("127.") or src_ip == "::1":
            continue

        stored_geo: Dict[str, Any] = {}
        if a.geolocation:
            try:
                stored_geo = json.loads(a.geolocation) if isinstance(a.geolocation, str) else (a.geolocation or {})
            except Exception:
                stored_geo = {}

        geo = _geo_for_ip(src_ip, stored_geo)

        key = src_ip   # group all alerts from same src_ip together
        if key not in points_map:
            points_map[key] = {
                "ip":              src_ip,
                "country":         geo.get("country", "Unknown"),
                "city":            geo.get("city", "Unknown"),
                "lat":             geo.get("lat", 0.0),
                "lon":             geo.get("lon", 0.0),
                "threat_category": a.threat_category,
                "risk_score":      a.risk_score,
                "count":           0
            }

        points_map[key]["count"] += 1
        if a.risk_score > points_map[key]["risk_score"]:
            points_map[key]["risk_score"] = a.risk_score
            points_map[key]["threat_category"] = a.threat_category

    return list(points_map.values())


@router.get("/api/v1/dashboard/weekly-report")
@router.get("/api/dashboard/weekly-report")
def get_weekly_report(
    week: str = Query("current", pattern="^(current|last_week|2_weeks_ago)$"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generates a full Weekly Report based on AlertORM and FlowORM records for the selected week.
    """
    now_dt = datetime.now(timezone.utc)
    current_mon = (now_dt - timedelta(days=now_dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    if week == "last_week":
        week_start_dt = current_mon - timedelta(days=7)
    elif week == "2_weeks_ago":
        week_start_dt = current_mon - timedelta(days=14)
    else:
        week_start_dt = current_mon

    week_end_dt = week_start_dt + timedelta(days=7)

    start_ts = week_start_dt.timestamp()
    end_ts = week_end_dt.timestamp()

    alerts = db.query(AlertORM).filter(
        AlertORM.created_ts >= start_ts,
        AlertORM.created_ts < end_ts
    ).all()

    daily_items = []
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(7):
        d_start_dt = week_start_dt + timedelta(days=i)
        d_end_dt = d_start_dt + timedelta(days=1)
        d_start_ts = d_start_dt.timestamp()
        d_end_ts = d_end_dt.timestamp()

        day_alerts = [a for a in alerts if d_start_ts <= a.created_ts < d_end_ts]

        crit = sum(1 for a in day_alerts if a.severity == "Critical")
        high = sum(1 for a in day_alerts if a.severity == "High")
        med = sum(1 for a in day_alerts if a.severity == "Medium")
        low = sum(1 for a in day_alerts if a.severity == "Low")

        daily_items.append({
            "day": day_names[i],
            "date_str": d_start_dt.strftime("%b %d"),
            "total_threats": len(day_alerts),
            "critical": crit,
            "high": high,
            "medium": med,
            "low": low
        })

    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    category_counts: Dict[str, int] = {}
    for a in alerts:
        sev = a.severity or "Low"
        if sev in severity_counts:
            severity_counts[sev] += 1
        cat = a.threat_category or "Anomaly"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    flow_ids = [a.flow_id for a in alerts]
    top_ips = []
    top_ports = []

    if flow_ids:
        ip_query = (
            db.query(FlowORM.src_ip, func.count(FlowORM.src_ip).label("count"))
            .filter(FlowORM.flow_id.in_(flow_ids))
            .group_by(FlowORM.src_ip)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )
        top_ips = [{"ip": r[0], "count": r[1]} for r in ip_query]

        port_query = (
            db.query(FlowORM.dst_port, func.count(FlowORM.dst_port).label("count"))
            .filter(FlowORM.flow_id.in_(flow_ids))
            .group_by(FlowORM.dst_port)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )
        top_ports = [{"port": r[0], "count": r[1]} for r in port_query]

    total_threats = len(alerts)
    avg_daily = round(total_threats / 7.0, 1)

    week_label_map = {
        "current": "Current Week",
        "last_week": "Last Week",
        "2_weeks_ago": "2 Weeks Ago"
    }

    return {
        "week_label": week_label_map.get(week, "Selected Week"),
        "start_date": week_start_dt.strftime("%Y-%m-%d"),
        "end_date": week_end_dt.strftime("%Y-%m-%d"),
        "total_threats": total_threats,
        "avg_daily_threats": avg_daily,
        "daily_breakdown": daily_items,
        "severity_breakdown": severity_counts,
        "category_breakdown": category_counts,
        "top_attacking_ips": top_ips,
        "top_attacked_ports": top_ports
    }
