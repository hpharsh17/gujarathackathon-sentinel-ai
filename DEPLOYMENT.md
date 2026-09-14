# Sentinel Vision AI — Enterprise Deployment & Operations Guide
### Gujarat Hackathon 2026 | Hybrid Model 2 (Unified AI) + Model 3 (VMS Federation)

Sentinel Vision AI is designed for mission-critical command centers. It can be deployed in two modes:
1. **Bare-Metal / Local Development Mode** (Windows / Linux with CUDA)
2. **Containerized Production Mode** (Docker & Docker Compose with NVIDIA GPU Passthrough)

---

## ⚡ Option 1: One-Click Windows Launcher (Recommended for Judges)

We have provided a unified Windows launcher script that manages all services from one interactive terminal:

```cmd
run_c2_system.bat
```

This menu allows you to choose:
- `[1]` **LAUNCH EVERYTHING IN 1-CLICK** (FastAPI + React GUI + AI Engine + Browser)
- `[2]` **Start React GUI + FastAPI Backend Only**
- `[3]` **Start Master AI Vision Pipeline Only** (`main.py`)
- `[4]` **Start FastAPI C2 Gateway Only** (`server.py`)
- `[5]` **Start React Tactical Frontend Only** (`npm run dev`)
- `[6]` **Docker Compose Deploy** (`docker compose up --build`)
- `[7]` **Exit**

---

## 🐳 Option 2: Docker Containerized Deployment (Phase 5)

Containerization eliminates missing host libraries (`ffmpeg`, OpenCV GUI, GLib) and ensures deterministic execution across any evaluation environment.

### Prerequisites:
- Docker Desktop or Docker Engine installed.
- NVIDIA Container Toolkit (`nvidia-container-toolkit`) installed for GPU passthrough.

### Single-Command Launch:
```bash
docker compose up --build
```

### What Docker Deploys:
1. **`sentinel_c2_backend`**:
   - Base image: `nvidia/cuda:11.8.0-runtime-ubuntu22.04`
   - Runs PyTorch with CUDA 11.8 on your NVIDIA GPU.
   - Hosts the FastAPI C2 Gateway and WebSockets on port `8000`.
2. **`sentinel_c2_frontend`**:
   - Node.js 20 Alpine container.
   - Hosts the React Cyberpunk Command & Control GUI on port `5173`.

---

## 💻 Option 3: Manual Step-by-Step Local Setup

### 1. Python AI Engine & Gateway
Activate your virtual environment and run the backend gateway:

```powershell
# Activate Virtualenv
.\.venv\Scripts\Activate.ps1

# Launch FastAPI Gateway
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive API Documentation: **http://localhost:8000/docs**
- Live Telemetry WebSocket: **ws://localhost:8000/ws/telemetry**

### 2. React Tactical C2 GUI
In a separate terminal, start the Vite development server:

```powershell
cd frontend
npm run dev
```
- Open browser at: **http://localhost:5173**

### 3. Master AI Vision Pipeline
Run the multi-camera 8-capability inference engine:

```powershell
python main.py
```
- Connects to the remote RTSP cameras (`cam01`, `cam08`, etc.)
- Ingests via in-memory lossy-drop FIFO queue (`frame_queue.py`)
- Runs real-time YOLO tracking and exports live metadata to `latest_event.json`.

---

## 🛡️ Department-Wise Role-Based Access Control (Model 3)

The C2 GUI provides an instant department switcher in the top navigation bar:
- **Police C2 (`POLICE`)**: Full access to all 30 Gujarat camera feeds, target scanning laser sweeps, and live Supabase stolen vehicle watchlist alerts.
- **Traffic Dept (`TRAFFIC`)**: Emphasizes traffic density, lane congestion, speeding indicators, and vehicle classification (Car, SUV, Truck, Bus, Motorcycle).
- **Municipal Corp (`MUNICIPAL`)**: Focuses on crowd density heatmaps, public safety monitoring, and municipal zoning.

---

## 📍 Gujarat GIS Mapping & Watchlist Integration

- **30 Geocoded Nodes**: All cameras are geocoded with real Gujarat coordinates (Ahmedabad, Junagadh, Mehsana, Navsari, Rajkot, Patan, Kutch).
- **Offline Fallback Registry**: If cloud connectivity is restricted during judging, `CameraDatabase` seamlessly falls back to the embedded in-memory registry (`LOCAL_REGISTRY`) without downtime.
- **Supabase Cloud Sync**: Live bidirectional sync for wanted plates (`stolen_vehicles`) and AI detection events.
