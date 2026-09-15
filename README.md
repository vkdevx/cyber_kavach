# 🛡️ CyberKavach — AI-Based Cyber Threat Detection & Defence System
### SIH Project ID: SIH26145

An AI-powered Network Threat Detection and Security Operations System capable of analyzing real-time network traffic, identifying multi-vector cyber attacks (Port Scan, DDoS, SYN Flood, Beaconing, C2), and providing actionable threat intelligence through an interactive SOC dashboard.

---

## 🌟 Key Features

- **Real-Time Packet Capture** — Live Wi-Fi/Ethernet traffic via Scapy
- **AI/ML Threat Detection:**
  - 🌲 Random Forest Classifier — Port Scan, DDoS, Brute Force, Infiltration
  - 🔍 Isolation Forest — zero-day anomaly detection
- **Smart False-Positive Suppression** — Normal browser traffic (Google, YouTube, Microsoft) never flagged
- **Interactive SOC Dashboard** — Live charts, threat map, network graph, real-time alerts
- **Threat Intelligence** — IP reputation feeds, CIDR correlation, TOR exit node detection
- **0% False Positive Rate** on normal browsing traffic

---

## ⚡ Quick Start (3 Steps)

```bash
# Step 1 — Clone
git clone https://github.com/vkdevx/cyber_kavach.git
cd cyber_kavach

# Step 2 — Auto Setup (creates venv, installs deps, creates .env)
python setup.py

# Step 3 — Run  (Windows: Run as Administrator)
python run_server.py
```

Then open **http://localhost:8000** in your browser.

> **Windows users:** Right-click → "Run as Administrator" for packet capture to work.
> **Linux/macOS users:** Use `sudo python run_server.py`

---

## 📋 Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | https://python.org/downloads — tick "Add to PATH" |
| Git | https://git-scm.com |
| **Npcap** (Windows only) | https://npcap.com/#download — tick "WinPcap API-compatible mode" |
| **libpcap** (Linux/macOS) | `sudo apt install libpcap-dev` or `brew install libpcap` |

---

## 🏗️ Architecture

```
Network Traffic (Live)
        │
        ▼
Packet Validator & Capture (Scapy)
        │
        ▼
Flow Aggregator & Feature Extractor
        │
        ▼
ML Inference Engine (RF + IsolationForest)
        │
        ▼
Risk Engine → FastAPI Backend + SQLite
        │
   ┌────┴────┐
   ▼         ▼
WebSocket   SOC Dashboard
Stream      (http://localhost:8000)
```

---

## 📂 Project Structure

```
cyber_kavach/
├── backend/                  # FastAPI Application
│   ├── api/                  # REST & WebSocket Endpoints
│   ├── core/                 # Auth, Security, Logging
│   ├── pipeline/             # Real-time Traffic Pipeline
│   └── risk/                 # Risk Engine & Explainability
├── config/                   # App Settings (settings.py)
├── data/threat_intel/        # GeoIP DB goes here
├── frontend/                 # SOC Web Dashboard (React + Chart.js)
├── ml/                       # Feature Extractors & Inference
├── models/trained/           # Pre-trained ML Models (.pkl)
├── network/                  # Packet Capture & Flow Aggregation
├── scripts/                  # Test simulators & seeding tools
├── storage/                  # SQLite ORM & Repositories
├── tests/                    # Unit & Integration Tests
├── setup.py                  # ✅ Auto setup (venv + deps + .env)
├── setup.bat                 # ✅ Windows double-click setup
├── run_server.py             # ✅ 1-click server starter
├── run_server.bat            # ✅ Windows double-click launcher
├── requirements.txt          # Python dependencies
└── .env.example              # Environment config template
```

---

## ⚙️ Manual Setup (if needed)

### 1 — Create virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### 3 — Configure environment
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env` and set your **network interface name**:
```env
# Windows PowerShell: Get-NetAdapter   →  use the "Name" column
CAPTURE_INTERFACE=Wi-Fi

# Linux: ip link show  →  usually eth0 or wlan0
CAPTURE_INTERFACE=wlan0
```

### 4 — (Optional) GeoIP for Threat Map
1. Register free at https://www.maxmind.com/en/geolite2/signup
2. Download **GeoLite2-City.mmdb**
3. Place it at: `data/threat_intel/GeoLite2-City.mmdb`

> The system runs fine without this — threat map just won't show locations.

### 5 — Start server
```bash
# Windows (run as Administrator)
python run_server.py

# Linux / macOS
sudo python run_server.py
```

---

## 🔄 Automated Git Version Control (Watchdog Auto-Sync)

CyberKavach includes an automated filesystem watcher that continuously monitors code changes, stages modified files, commits with timestamps, and pushes directly to GitHub:

```bash
# Start auto-git synchronizer (Windows / Linux / macOS)
python auto_commit_watcher.py

# Or on Windows, double click:
run_git_watcher.bat
```

- **Debounced Pushes**: Waits 3.0s after edits to consolidate multiple rapid saves into a single clean commit.
- **Smart Filtering**: Automatically ignores databases (`*.db`), virtual environments (`venv/`), secrets (`.env`), and cache.

---

## 🛡️ Detection Engine & Attack Signatures

CyberKavach operates at the raw network interface level (independent of Windows Defender Firewall state):

| Attack Vector | Signature & Detection Criteria |
|---|---|
| **Nmap SYN Scan (`-sS`)** | Incomplete 3-way handshake (SYN sent, 0% ACK follow-through), ≥2 destination ports |
| **Stealth XMAS Scan** | Malformed packet probes with FIN + PSH + URG flags set simultaneously |
| **Stealth NULL Scan** | Packet probes with 0 TCP flags set to trigger kernel RST responses |
| **Stealth FIN Scan** | Lone FIN packets without prior established state |
| **SYN Flood / DoS** | Machine-rate bursts of tiny packets (<120B) with >85% TCP SYN ratio |
| **Zero-Day Anomalies** | Unsupervised Isolation Forest outlier scoring on statistical flow deviations |
| **Benign Web Traffic** | 0% false positives — Whitelisted standard server responses (80, 443, 53) |

---

## 🌐 Cloudflare Tunnel (Share Dashboard Publicly)

```bash
# Windows (cloudflared.exe included in repo)
.\cloudflared.exe tunnel --url http://localhost:8000

# Linux / macOS
cloudflared tunnel --url http://localhost:8000
```

Gives a public HTTPS URL: `https://xxxx.trycloudflare.com`

---

## 🌐 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | SOC Dashboard (Web UI) |
| `GET /api/alerts` | All threat alerts |
| `GET /api/flows` | Network flow records |
| `GET /api/stats` | System statistics |
| `GET /api/threats/timeline` | Threat timeline chart |
| `GET /api/threats/categories` | Category breakdown |
| `GET /api/threats/protocols` | Protocol distribution |
| `GET /api/threats/geoip` | Geographic threat data |
| `GET /api/health` | System health status |
| `WS /ws` | WebSocket real-time stream |

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named scapy` | Run `pip install -r requirements.txt` |
| `PermissionError` on capture | Windows: Run as Admin. Linux: `sudo` |
| `Interface not found` | Set correct `CAPTURE_INTERFACE` in `.env` |
| `Port 8000 in use` | `netstat -ano \| findstr 8000` then `taskkill /PID <id> /F` |
| GeoIP map not showing | Download GeoLite2-City.mmdb (see Step 4 above) |
| `sklearn version warning` | Harmless — models still work fine |
| Nmap not detected | Ensure server runs as Administrator (Windows) |

---

## 🧪 Testing

```bash
# Test false-positive rate (should = 0 alerts on normal traffic)
python scripts/normal_traffic.py

# Simulate port scan attack
python scripts/simulate_attack.py

# Run unit tests
pytest
```

---

## 📜 License

MIT License — Free to use, modify, and distribute.

---

## 👥 Team

**SIH26145 — CyberKavach**
AI-Based Cyber Threat Detection & Defence System
