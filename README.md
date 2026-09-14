# Sentinel Vision AI

Sentinel Vision AI is a multi-camera command-and-control system for the Gujarat Police Innovation Hackathon. It combines a FastAPI gateway, a React tactical dashboard, real-time RTSP ingestion, and AI-assisted detection for vehicles, license plates, crowd flow, accidents, faces, and suspicious activity.

## Prerequisites

### Required for local setup

- Python 3.10 or newer
- Node.js 20 or newer and npm
- Git
- FFmpeg and the native OpenCV libraries required by your operating system
- An NVIDIA GPU with compatible drivers is recommended for real-time inference

### Required for Docker setup

- Docker Desktop or Docker Engine with Compose
- NVIDIA Container Toolkit and an NVIDIA GPU for GPU inference

The backend can run without a GPU, but model inference and multiple RTSP streams may be slower.

## Configure Environment Variables

Create or update `.env` in the project root:

```dotenv
SENTINEL_EMAIL=your-camera-account-email
SENTINEL_RTSP_PASSWORD=your-camera-account-password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

Keep `.env` private. Do not commit camera passwords, Supabase keys, or database passwords to source control. If credentials have been shared publicly, rotate them before deployment.

## Start Without Docker

### Windows one-click launcher

From the project root, run:

```bat
run_c2_system.bat
```

Choose one of these modes:

- `1` - start the backend, frontend, and headless AI pipeline.
- `2` - start only the backend and frontend.
- `3` - start the AI pipeline.
- `4` - start the FastAPI backend.
- `5` - start the React frontend.

The launcher expects a virtual environment at `.venv` for the Python commands.

### Manual local setup

Create and activate a Python virtual environment from the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install and start the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Start the FastAPI gateway in another terminal from the project root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Start the AI pipeline when camera inference is required:

```powershell
python main.py --headless
```

For the OpenCV desktop view instead of the browser relay, run `python main.py` without `--headless`.

## Start With Docker

From the project root, build and start the Compose stack:

```powershell
docker compose up --build
```

To run it in the background:

```powershell
docker compose up --build -d
```

Stop the stack with:

```powershell
docker compose down
```

The Compose configuration starts:

- `sentinel-backend` on `http://localhost:8000`
- `sentinel-frontend` on `http://localhost:5173`

The backend image uses CUDA 11.8 and installs the Docker-specific dependencies from `requirements-docker.txt`. The repository and model checkpoints are mounted into the backend container, so local changes are visible while it is running.

## Service URLs

| Service | URL |
| --- | --- |
| Tactical dashboard | http://localhost:5173 |
| FastAPI API | http://localhost:8000 |
| Swagger API docs | http://localhost:8000/docs |
| ReDoc API docs | http://localhost:8000/redoc |
| Telemetry WebSocket | `ws://localhost:8000/ws/telemetry` |

## Camera and AI Notes

1. Add camera IDs to `active_cameras.json`, for example:

   ```json
   ["cam01", "cam08"]
   ```

2. Ensure the RTSP credentials in `.env` are valid and the machine can reach the camera server.
3. The API can serve cached frames from `frames_cache/` even when the inference process is not running.
4. Model files must be present in `checkpoints/` before starting `main.py`.

The application also includes local fallback camera metadata when cloud connectivity is unavailable. Supabase-backed features require valid Supabase configuration.

## Troubleshooting

- **Port already in use:** stop the process using port `8000` or `5173`, or change the corresponding launch command.
- **PowerShell blocks activation:** run `Set-ExecutionPolicy -Scope Process Bypass` in the current PowerShell window, then activate `.venv` again.
- **No camera frames:** verify `.env`, network access to the RTSP server, and the IDs in `active_cameras.json`.
- **Slow inference or CUDA errors:** verify NVIDIA drivers and the installed PyTorch build; use CPU-compatible dependencies if running without an NVIDIA GPU.
- **Docker GPU unavailable:** verify Docker Desktop GPU support and NVIDIA Container Toolkit installation.

## Additional Documentation

- [Deployment guide](DEPLOYMENT.md)
- [System architecture](SYSTEM_ARCHITECTURE.md)
- [Master plan](MASTER_PLAN.md)

## Project Layout

- `server.py` - FastAPI gateway, camera controls, MJPEG streams, and telemetry WebSocket.
- `main.py` - master AI inference and multi-camera processing pipeline.
- `frontend/` - React + Vite command dashboard.
- `models/` - detection and classification modules.
- `checkpoints/` - local model weights.
- `frames_cache/` - generated camera frames.
- `active_cameras.json` - cameras currently selected for processing.
- `run_c2_system.bat` - Windows launcher menu.
