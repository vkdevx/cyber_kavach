from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# --- Authentication Schemas ---

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    password: str = Field(..., min_length=8, max_length=100)
    role: Optional[str] = Field("analyst", pattern="^(analyst|admin)$")


class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_ts: float


# --- System & Status Schemas ---

class SystemStatusResponse(BaseModel):
    status: str
    listening: bool
    degraded: bool
    interface: str
    zero_outbound_guarantee: bool
    timestamp: float


class LiveStatsResponse(BaseModel):
    total_packets: int
    total_flows: int
    safe_flows: int
    suspicious_flows: int
    active_threat_level: str
    protocol_breakdown: Dict[str, int]


class ModelStatusResponse(BaseModel):
    supervised_model: Dict[str, str]
    unsupervised_model: Dict[str, str]
    degraded_mode: bool


# --- Alert Schemas ---

class GeolocationInfo(BaseModel):
    country: Optional[str] = "Unknown"
    state: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    is_approximate: bool = True


class AlertResponse(BaseModel):
    alert_id: str
    correlation_id: str
    flow_id: str
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    risk_score: int
    severity: str
    confidence: float
    threat_category: str
    explanation: str
    top_features: List[str]
    geolocation: GeolocationInfo
    status: str
    notes: Optional[str] = ""
    created_ts: float


class AlertStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(acknowledged|false_positive)$")


class AlertNotesUpdateRequest(BaseModel):
    notes: str


class AlertHistoryResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int


# --- Simulator & PCAP Schemas ---

class SimulatorCommandResponse(BaseModel):
    success: bool
    message: str
    scenario: Optional[str] = None


class PcapUploadResponse(BaseModel):
    filename: str
    status: str
    flows_parsed: int


# --- Dashboard Chart & Weekly Report Schemas ---

class ThreatTimepoint(BaseModel):
    timestamp: str
    total_threats: int
    critical: int
    high: int
    medium: int
    low: int


class ThreatTimelineResponse(BaseModel):
    timeframe: str
    timepoints: List[ThreatTimepoint]
    total_in_window: int


class CategoryItem(BaseModel):
    category: str
    count: int
    percentage: float


class CategoryBreakdownResponse(BaseModel):
    timeframe: str
    categories: List[CategoryItem]
    total_threats: int


class AttackMapPoint(BaseModel):
    ip: str
    country: str
    city: str
    lat: float
    lon: float
    threat_category: str
    risk_score: int
    count: int


class WeeklyReportDayItem(BaseModel):
    day: str
    date_str: str
    total_threats: int
    critical: int
    high: int
    medium: int
    low: int


class WeeklyReportResponse(BaseModel):
    week_label: str
    start_date: str
    end_date: str
    total_threats: int
    avg_daily_threats: float
    daily_breakdown: List[WeeklyReportDayItem]
    severity_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    top_attacking_ips: List[Dict[str, Any]]
    top_attacked_ports: List[Dict[str, Any]]

