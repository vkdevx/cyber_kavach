# OneWay Sentinel — Attack Scenarios & Traffic Baseline Specification (`attack-scenarios.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`master-prd.md:198`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/master-prd.md#L198), [`architecture.md:520`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md#L520), and [`rules.md:529`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L529).

---

## 1. Traffic Baseline & Attack Simulation Overview

OneWay Sentinel supports dual demonstration paths:
1. **Synthetic Simulator (Primary, Standalone):** In-memory event emitters in `simulator/scenarios/` that generate flow records matching statistical attack signatures. Works 100% offline without network infrastructure.
2. **Kali Linux Controlled Lab (Authentic Demo):** Real attack commands executed from a Kali Linux attacker VM against an isolated lab target host on a host-only virtual network, captured via SPAN/mirror port by OneWay Sentinel.

---

## 2. Normal Traffic Baseline

* **Description:** Represents legitimate operational traffic traversing the diode link (e.g. periodic sensor telemetry, NTP sync, DNS queries, web browsing, file sync).
* **Statistical Signature:**
  - Packet count: 10 – 50 packets / 5s window.
  - Inter-arrival time (IAT): Variable ($0.05\text{s} - 1.5\text{s}$), non-rigid.
  - Destination ports: Standard ports (80, 443, 53, 123).
  - Byte entropy: Moderate.
* **Simulator Implementation:** `simulator/normal_traffic_simulator.py`
* **Kali Lab Reproduction:** Standard HTTP requests, ping sweeps, and background wget loops against lab target.

---

## 3. Threat Scenarios & Detection Signatures

### Scenario 1: Port Scanning
* **Detection Objective:** Reconnaissance against a single target host attempting to identify open services.
* **Statistical Signature:** Single source IP $\rightarrow$ Single dest IP across **many distinct dest ports** (>20 unique ports in 5s). Low byte count per flow.
* **Expected Output:** Severity `High`, Category `Port Scanning`.
* **Simulator File:** `simulator/scenarios/port_scan.py`
* **Kali Linux Command:**
  ```bash
  # Fast SYN port scan against isolated lab target IP
  nmap -sS -p 1-1000 -T4 192.168.56.101
  ```

### Scenario 2: Network / Subnet Scanning
* **Detection Objective:** Reconnaissance across an IP range to map live hosts.
* **Statistical Signature:** Single source IP $\rightarrow$ **many distinct dest IPs** (>15 unique IPs in 5s) on a consistent port (e.g. 80, 443, 22).
* **Expected Output:** Severity `Medium`, Category `Network Scanning`.
* **Simulator File:** `simulator/scenarios/network_scan.py`
* **Kali Linux Command:**
  ```bash
  # Ping sweep / host discovery across lab subnet
  nmap -sn 192.168.56.0/24
  ```

### Scenario 3: Volumetric DDoS / SYN Flood
* **Detection Objective:** High-volume traffic flood intended to overwhelm a destination host.
* **Statistical Signature:** Extremely high packet rate (>500 pkts/5s), low/uniform inter-arrival time ($\text{mean IAT} < 0.005\text{s}$), uniform small packet size.
* **Expected Output:** Severity `Critical`, Category `DDoS-like Volumetric Behavior`.
* **Simulator File:** `simulator/scenarios/ddos_volumetric.py`
* **Kali Linux Command:**
  ```bash
  # SYN flood targeting port 80 of isolated lab host
  hping3 --flood --syn -p 80 192.168.56.101
  ```

### Scenario 4: Data Exfiltration (Volume Anomaly)
* **Detection Objective:** Unauthorized large outbound data transfer from an internal source.
* **Statistical Signature:** Unusually high outbound byte count (>10 MB in 5s) relative to learned source baseline; packet size skewed to maximum MTU (~1500 bytes).
* **Expected Output:** Severity `Critical`, Category `Data Exfiltration`.
* **Simulator File:** `simulator/scenarios/exfiltration.py`
* **Kali Linux Command:**
  ```bash
  # High-volume outbound binary stream to lab target
  nc -w 3 192.168.56.101 9999 < /dev/urandom
  ```

### Scenario 5: Command-and-Control (C2) Beaconing
* **Detection Objective:** Covert channel periodic communication to an external endpoint.
* **Statistical Signature:** Low byte count, rigid/constant inter-arrival timing ($\text{IAT variance} \approx 0.0001$), regular 1-second pulse to a single destination.
* **Expected Output:** Severity `Medium`, Category `Beaconing` or `Unknown Anomaly`.
* **Simulator File:** `simulator/scenarios/beaconing.py`
* **Kali Linux Command:**
  ```bash
  # Strict 1-second periodic HTTP beacon script
  while true; do curl -s http://192.168.56.101/heartbeat > /dev/null; sleep 1; done
  ```

### Scenario 6: Unknown Anomaly (Covert Channel Outlier)
* **Detection Objective:** Novel attack or covert channel deviating statistically from baseline without matching a known supervised signature.
* **Statistical Signature:** Rare protocol/port combination, unusual byte-entropy distribution.
* **Expected Output:** Flagged by Isolation Forest, Severity `Medium`–`High`, Category `Unknown Anomaly`.
* **Simulator File:** `simulator/scenarios/unknown_anomaly.py`

---

## 4. Scope Constraints & Out-of-Scope Attacks (TBD / Excluded)

| Attack Type | Status | Technical Constraint / Explanation |
|---|---|---|
| **Brute-Force Password Attacks** | **OUT OF SCOPE** | Requires counting failed HTTP 401/SSH response codes. On a unidirectional diode link, response codes are physically invisible (`master-prd.md:60`). |
| **SQL Injection (SQLi)** | **EXCLUDED FROM DPI** | Payload inspection is disabled for privacy and performance (`master-prd.md:58`). SQLi is evaluated purely as a volumetric/entropy metadata anomaly. |
| **Active Blocking Verification** | **PROHIBITED** | OneWay Sentinel is detect-only. No TCP resets or firewall blocks can be triggered on the diode link (`rules.md:395`). |
