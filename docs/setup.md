# OneWay Sentinel — Setup & Execution Guide (`setup.md`)

**Product:** OneWay Sentinel — AI-Based Detection of Cyber Threats in Unidirectional IP Traffic (SIH26145)  
**Governance:** Governed by [`architecture.md:257`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/architecture.md#L257) and [`rules.md:523`](file:///c:/Users/KCFL-4/Desktop/CyberThreatDetection/docs/rules.md#L523).

---

## 1. Prerequisites

- **Operating System:** Linux / macOS / Windows (WSL2 recommended for Scapy raw socket capture).
- **Python:** Version 3.11 or higher.
- **Node.js:** Version 18.0 or higher (with `npm` v9+).
- **Git:** For version control.

---

## 2. Environment Setup

### 2.1 Backend Setup (Python)

1. Clone or navigate to the repository workspace:
   ```bash
   cd CyberThreatDetection
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. Install backend dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

### 2.2 Frontend Setup (React / Vite)

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```

### 2.3 Offline Training Environment Setup (Isolated Python Environment)

To train and experiment with machine learning models separately from the live application runtime:

1. Create a separate dedicated virtual environment for ML training:
   ```bash
   python3.11 -m venv venv-training
   source venv-training/bin/activate   # On Windows: venv-training\Scripts\activate
   ```
2. Install offline training dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r training/requirements.txt
   ```
3. Folder Structure:
   - `/training/notebooks/`: Jupyter notebooks for exploratory data analysis (EDA) and model prototyping.
   - `/training/scripts/`: Standalone dataset conversion and model training scripts.
   - `/training/reports/`: Evaluation reports, confusion matrices, ROC curve plots, and feature importance summaries.

---

## 3. Dataset Preprocessing & Model Training

To train the machine learning models offline before launching the application:

1. Download public IDS dataset (e.g. CICIDS2017) to `datasets/raw/` (or run `scripts/download_datasets.sh`).
2. Run forward-flow filtering and feature extraction:
   ```bash
   python -m datasets.pipeline.forward_flow_filter
   ```
3. Train Random Forest and Isolation Forest models:
   ```bash
   python -m ml.supervised.train_supervised
   python -m ml.unsupervised.train_unsupervised
   ```
   *Artifacts will be written to `models/trained/random_forest_v1.pkl` and `isolation_forest_v1.pkl`.*

---

## 4. Running Development Servers

### Option A: Running Backend & Frontend Together
Run the development launch script:
```bash
bash scripts/run_dev.sh
```

### Option B: Running Manually

1. **Start Backend (FastAPI + Uvicorn):**
   ```bash
   # From project root
   uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - API Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/api/status`

2. **Start Frontend (Vite Dev Server):**
   ```bash
   cd frontend
   npm run dev
   ```
   - Main Dashboard: `http://localhost:5173`

---

## 5. Verification Commands

### 5.1 Zero-Outbound Guarantee Verification
Run the mandatory zero-outbound static grep and runtime socket assertion:
```bash
python scripts/verify_zero_outbound.py
pytest tests/network/test_zero_outbound.py
```

### 5.2 Automated Test Suite
Run unit, ML inference, API, and integration tests:
```bash
pytest tests/
```

---

## 6. Live SIH Demonstration Mode

For offline judging demonstrations without live network dependencies:
```bash
bash scripts/run_demo.sh
```
This launches the system pre-configured with synthetic simulator traffic enabled. Presenters can select and trigger attack scenarios directly from the dashboard's `SimulatorControls` panel.
