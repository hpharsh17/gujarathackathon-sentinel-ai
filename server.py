"""
Sentinel Vision AI - C2 Backend Gateway
Simple, direct per-camera RTSP workers — no delays, no limits, no complexity.
"""

import os
import cv2
import json
import time
import asyncio
import threading
import numpy as np
from typing import Optional, List, Dict
from urllib.parse import quote
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

from database import CameraDatabase

load_dotenv()

app = FastAPI(title="Sentinel Vision AI - C2 API Gateway", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

db = CameraDatabase()

FRAMES_CACHE_DIR = "frames_cache"
os.makedirs(FRAMES_CACHE_DIR, exist_ok=True)
CONFIG_FILE = "active_cameras.json"


# ── helpers ──────────────────────────────────────────────────────────────────
def build_rtsp_url(camera_id: str) -> str:
    email    = quote(os.getenv("SENTINEL_EMAIL", ""), safe="")
    password = quote(os.getenv("SENTINEL_RTSP_PASSWORD", ""), safe="")
    return f"rtsp://{email}:{password}@103.250.160.189:8554/stream/{camera_id}"


def get_active_cameras() -> List[str]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                d = json.load(f)
                if isinstance(d, list):
                    return d
        except Exception:
            pass
    return ["cam01"]


def save_active_cameras(cams: List[str]):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cams, f, indent=2)


# ── per-camera worker ─────────────────────────────────────────────────────────
class CameraWorker:
    def __init__(self, camera_id: str):
        self.camera_id  = camera_id.lower()
        self.status     = "CONNECTING"
        self.fps_actual = 0.0
        self.is_running = True
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name=f"cam-{self.camera_id}")
        self._thread.start()

    def _placeholder(self, msg: str = "") -> bytes:
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        img[:] = (10, 8, 5)
        cv2.rectangle(img, (2, 2), (637, 357), (0, 100, 70), 1)
        cv2.putText(img, f"[ {self.camera_id.upper()} ]",
                    (24, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 243, 255), 2)
        cv2.putText(img, msg or "CONNECTING...",
                    (24, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 150, 40), 1)
        cv2.putText(img, time.strftime("%H:%M:%S"),
                    (24, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 180, 60), 1)
        _, buf = cv2.imencode(".jpg", img)
        return buf.tobytes()

    def _write(self, data: bytes):
        tmp = os.path.join(FRAMES_CACHE_DIR, f"{self.camera_id}_tmp.jpg")
        dst = os.path.join(FRAMES_CACHE_DIR, f"{self.camera_id}.jpg")
        try:
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, dst)
        except Exception:
            pass

    def _run(self):
        cid = self.camera_id
        self._write(self._placeholder())

        while self.is_running:
            self.status = "CONNECTING"
            url = build_rtsp_url(cid)

            # FFMPEG options — TCP transport, keep trying
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;tcp|buffer_size;4194304|max_delay;500000"
            )

            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                print(f"[{cid}] RTSP failed, retrying in 5s...")
                self._write(self._placeholder("RTSP FAILED — RETRYING..."))
                time.sleep(5)
                continue

            print(f"[{cid}] Stream connected ✓")
            self.status = "ONLINE"
            t0 = time.time()
            frames = 0
            fails  = 0

            while self.is_running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    fails += 1
                    if fails > 60:
                        print(f"[{cid}] Stream lost, reconnecting...")
                        break
                    time.sleep(0.05)
                    continue

                fails = 0
                frames += 1
                elapsed = time.time() - t0
                if elapsed >= 2.0:
                    self.fps_actual = frames / elapsed
                    frames = 0
                    t0 = time.time()

                # HUD overlay
                ts = time.strftime("%H:%M:%S")
                h, w = frame.shape[:2]
                cv2.rectangle(frame, (0, 0), (w, 30), (0, 0, 0), -1)
                cv2.putText(frame, f"LIVE: {cid.upper()}  {ts}",
                            (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 243, 255), 2)

                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                self._write(buf.tobytes())
                time.sleep(0.033)  # ~30fps write cap

            cap.release()
            if self.is_running:
                self.status = "CONNECTING"
                time.sleep(2)

        self.status = "STOPPED"
        print(f"[{self.camera_id}] Worker stopped")

    def stop(self):
        self.is_running = False


# ── worker registry ───────────────────────────────────────────────────────────
_workers: Dict[str, CameraWorker] = {}
_lock = threading.Lock()


def sync_workers():
    """Start/stop workers to match active_cameras.json exactly."""
    desired = set(get_active_cameras())
    with _lock:
        # stop removed
        for cid in list(_workers):
            if cid not in desired:
                _workers[cid].stop()
                del _workers[cid]
                try:
                    os.remove(os.path.join(FRAMES_CACHE_DIR, f"{cid}.jpg"))
                except FileNotFoundError:
                    pass
        # start new
        for cid in desired:
            if cid not in _workers:
                _workers[cid] = CameraWorker(cid)


# Boot workers
sync_workers()


# ── pydantic models ───────────────────────────────────────────────────────────
class TogglePayload(BaseModel):
    camera_id: str
    active: bool


# ── routes ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"system": "Sentinel Vision AI C2 Gateway", "status": "OPERATIONAL"}


@app.get("/api/active-cameras")
async def get_active_cameras_api():
    return get_active_cameras()


@app.post("/api/active-cameras/toggle")
async def toggle_camera(payload: TogglePayload):
    cid  = payload.camera_id.lower()
    cams = get_active_cameras()
    if payload.active:
        if cid not in cams:
            cams.append(cid)
    else:
        if cid in cams:
            cams.remove(cid)
    save_active_cameras(cams)
    sync_workers()
    return {"status": "OK", "active_cameras": cams}


@app.get("/api/cameras")
async def get_cameras():
    active = set(get_active_cameras())

    latest_ai: dict = {}
    if os.path.exists("latest_event.json"):
        try:
            with open("latest_event.json") as f:
                ev = json.load(f)
                latest_ai = ev.get("ai_detections", {})
        except Exception:
            pass

    cameras = []
    for cid, cam in CameraDatabase.LOCAL_REGISTRY.items():
        is_active = cid in active
        worker    = _workers.get(cid)

        if is_active and worker:
            status = worker.status
            fps    = round(worker.fps_actual, 1)
            v_cnt  = len(latest_ai.get("vehicles", [])) if status == "ONLINE" else None
            p_cnt  = latest_ai.get("people_count", 0)  if status == "ONLINE" else None
        else:
            status = "STANDBY"
            fps    = 0
            v_cnt  = None
            p_cnt  = None

        cameras.append({
            "camera_id":     cid,
            "location_name": cam.get("location_name", "Unknown"),
            "district":      cam.get("district", "Gujarat"),
            "latitude":      cam.get("latitude"),
            "longitude":     cam.get("longitude"),
            "maps_link":     cam.get("maps_link"),
            "status":        status,
            "fps":           fps,
            "is_active":     is_active,
            "vehicle_count": v_cnt,
            "people_count":  p_cnt,
        })
    return cameras


@app.get("/api/events/latest")
async def get_latest_event():
    if os.path.exists("latest_event.json"):
        try:
            with open("latest_event.json") as f:
                return json.load(f)
        except Exception:
            pass
    return {"camera_id": "cam01", "ai_detections": {
        "people_count": 0, "vehicles": [], "license_plates": [], "alerts": []
    }}


@app.get("/api/telemetry")
async def get_telemetry():
    streaming = [cid for cid, w in _workers.items() if w.status == "ONLINE"]
    return {
        "active_cameras":    get_active_cameras(),
        "streaming_cameras": streaming,
        "total_nodes":       30,
        "server_time":       time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _placeholder_bytes(camera_id: str) -> bytes:
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    img[:] = (10, 8, 5)
    cv2.rectangle(img, (2, 2), (637, 357), (0, 100, 70), 1)
    cv2.putText(img, f"[ {camera_id.upper()} ]",
                (24, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 243, 255), 2)
    cv2.putText(img, "STANDBY", (24, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 80), 1)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


@app.get("/api/frame/{camera_id}")
async def get_frame(camera_id: str):
    path = os.path.join(FRAMES_CACHE_DIR, f"{camera_id.lower()}.jpg")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return Response(content=f.read(), media_type="image/jpeg")
    return Response(content=_placeholder_bytes(camera_id), media_type="image/jpeg")


@app.get("/api/stream/{camera_id}")
async def stream(camera_id: str):
    """MJPEG stream for this camera only — never cross-feeds."""
    cid  = camera_id.lower()
    path = os.path.join(FRAMES_CACHE_DIR, f"{cid}.jpg")

    def gen():
        while True:
            data = None
            if os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        data = f.read()
                except Exception:
                    pass
            if not data or len(data) < 500:
                data = _placeholder_bytes(cid)
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + data + b"\r\n"
            time.sleep(0.04)  # ~25 fps serve rate

    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            streaming = [cid for cid, w in _workers.items() if w.status == "ONLINE"]
            await ws.send_json({
                "timestamp":         time.time(),
                "time_str":          time.strftime("%H:%M:%S"),
                "streaming_cameras": streaming,
                "active_cameras":    get_active_cameras(),
            })
            await asyncio.sleep(1.0)
    except (WebSocketDisconnect, Exception):
        pass


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*55)
    print("  SENTINEL VISION AI — C2 FASTAPI GATEWAY")
    print("  Docs: http://127.0.0.1:8000/docs")
    print("="*55 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
