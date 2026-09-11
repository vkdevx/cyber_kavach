# OneWay Sentinel — REST & WebSocket API Specification (`api.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`architecture.md:480`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md#L480) and [`rules.md:318`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L318).

---

## 1. API Architecture & Standards

The OneWay Sentinel API is served by **FastAPI** (`backend/api/main.py`). All REST endpoints consume and produce JSON payloads validated via Pydantic v2 schemas (`backend/api/schemas.py`). Real-time alert streaming and system telemetry use native WebSockets (`/ws/alerts`).

- **Base URL:** `http://localhost:8000/api`
- **WebSocket URL:** `ws://localhost:8000/ws/alerts`
- **Error Format:** All HTTP error responses (4xx/5xx) return a standard payload:
  ```json
  {
    "detail": {
      "code": "ALERT_NOT_FOUND",
      "message": "Alert with ID 'alt_123' does not exist."
    }
  }
  ```

---

## 2. Authentication Routes (`/api/auth`)

#### `POST /api/auth/register`
* **Purpose:** Register a new user account.
* **Request Body:** `{"username": "john_analyst", "email": "john@sentinel.local", "password": "SecurePassword123!", "role": "analyst"}`
* **Response `201 Created`:** `{"user_id": "usr_123", "username": "john_analyst", "email": "john@sentinel.local", "role": "analyst", "is_active": true, "created_ts": 1772524800.0}`

#### `POST /api/auth/login`
* **Purpose:** Authenticate credentials and receive access + refresh JWT tokens.
* **Request Body:** `{"username_or_email": "john_analyst", "password": "SecurePassword123!"}`
* **Response `200 OK`:** `{"access_token": "eyJhbG...", "refresh_token": "eyJhbG...", "token_type": "bearer", "expires_in": 3600}`

#### `POST /api/auth/refresh`
* **Purpose:** Issue a new access token using a valid refresh token.
* **Request Body:** `{"refresh_token": "eyJhbG..."}`
* **Response `200 OK`:** Token response object.

#### `POST /api/auth/logout`
* **Purpose:** Log out user and log security audit event.
* **Response `200 OK`:** `{"message": "Successfully logged out."}`

#### `GET /api/auth/me`
* **Purpose:** Retrieve profile of currently authenticated user.
* **Response `200 OK`:** User response object.

---

## 3. System & Telemetry Routes

#### `GET /api/status`
* **Purpose:** System operational status and zero-outbound diode integrity check.
* **Response `200 OK`:**
  ```json
  {
    "status": "healthy",
    "listening": true,
    "degraded": false,
    "interface": "eth0 (promisc, read-only)",
    "zero_outbound_guarantee": true,
    "timestamp": 1772524800.0
  }
  ```

#### `GET /api/stats/live`
* **Purpose:** Real-time volumetric overview and threat breakdown.
* **Response `200 OK`:**
  ```json
  {
    "total_packets": 142500,
    "total_flows": 12540,
    "safe_flows": 11930,
    "suspicious_flows": 610,
    "active_threat_level": "High",
    "protocol_breakdown": { "tcp": 8500, "udp": 3500, "icmp": 540 }
  }
  ```

#### `GET /api/models/status`
* **Purpose:** ML model versions and inference health status.
* **Response `200 OK`:**
  ```json
  {
    "supervised_model": {
      "name": "Random Forest Classifier",
      "version": "v1.0",
      "status": "loaded"
    },
    "unsupervised_model": {
      "name": "Isolation Forest",
      "version": "v1.0",
      "status": "loaded"
    },
    "degraded_mode": false
  }
  ```

---

### 2.2 Alert Management Routes

#### `GET /api/alerts`
* **Purpose:** Get recent active alerts (LiveAlertFeed hydration).
* **Query Params:** `limit` (int, default=50)
* **Response `200 OK`:**
  ```json
  [
    {
      "alert_id": "alt_881",
      "correlation_id": "corr_992",
      "flow_id": "flw_102",
      "risk_score": 92,
      "severity": "Critical",
      "confidence": 0.89,
      "threat_category": "DDoS-like Volumetric Behavior",
      "explanation": "Packet rate is 15x learned baseline; IAT variance is unusually uniform.",
      "top_features": ["total_packets", "mean_iat"],
      "geolocation": { "country": "Germany", "city": "Frankfurt", "is_approximate": true },
      "status": "new",
      "created_ts": 1772524795.0
    }
  ]
  ```

#### `GET /api/alerts/{id}`
* **Purpose:** Full detail view for a specific alert.
* **Response `200 OK`:** Detailed alert object including full flow metadata, 13-feature vector, model output scores, and explanation.

#### `POST /api/alerts/{id}/ack`
* **Purpose:** Mark an alert as acknowledged.
* **Response `200 OK`:** `{"alert_id": "alt_881", "status": "acknowledged"}`

#### `POST /api/alerts/{id}/false-positive`
* **Purpose:** Mark an alert as a false positive.
* **Response `200 OK`:** `{"alert_id": "alt_881", "status": "false_positive"}`

#### `POST /api/alerts/{id}/notes`
* **Request Body:** `{"notes": "Investigated by analyst. Normal backup script."}`
* **Response `200 OK`:** `{"alert_id": "alt_881", "notes_updated": true}`

#### `GET /api/alerts/history`
* **Purpose:** Search and filter historical alert logs.
* **Query Params:** `start_date`, `end_date`, `category`, `severity`, `src_ip`, `status`, `page`, `page_size`.
* **Response `200 OK`:**
  ```json
  {
    "items": [...],
    "total": 342,
    "page": 1,
    "page_size": 25
  }
  ```

---

### 2.3 Simulator & Ingestion Routes

#### `POST /api/simulator/normal/start` & `/stop`
* **Purpose:** Start/stop the background synthetic baseline traffic emitter.

#### `POST /api/simulator/attack/{scenario}/start` & `/stop`
* **Path Param:** `scenario` (`port_scan`, `network_scan`, `ddos_volumetric`, `exfiltration`, `beaconing`, `unknown_anomaly`)

#### `POST /api/pcap/upload`
* **Request:** Multipart form upload (`.pcap` file)
* **Response `200 OK`:** `{"filename": "capture.pcap", "status": "processing", "flows_parsed": 120}`

#### `GET /api/geolocation/{ip}`
* **Response `200 OK`:**
  ```json
  {
    "ip": "198.51.100.45",
    "country": "Germany",
    "state": "Hesse",
    "city": "Frankfurt",
    "lat": 50.1109,
    "lon": 8.6821,
    "is_approximate": true
  }
  ```

---

### 2.4 WebSocket Real-Time Telemetry Contract

#### `WS /ws/alerts`
* **Purpose:** Bidirectional real-time stream for telemetry updates and instant alert notifications.
* **Stream Event Payload (`AlertEvent`):**
  ```json
  {
    "event_type": "ALERT_NEW",
    "payload": {
      "alert_id": "alt_902",
      "correlation_id": "corr_331",
      "src_ip": "192.168.1.45",
      "dst_ip": "10.0.0.5",
      "protocol": "TCP",
      "risk_score": 85,
      "severity": "Critical",
      "threat_category": "Port Scanning",
      "explanation": "Destination port diversity is 9x learned baseline.",
      "timestamp": 1772524810.0
    }
  }
  ```
