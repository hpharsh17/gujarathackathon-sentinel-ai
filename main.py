"""
Sentinel Vision AI - Master Execution Engine
Dynamic Multi-Camera Real-Time Ingestion and AI Inference Engine.
Reads active camera selections from active_cameras.json in real time,
streams annotated frames to frames_cache/, and exports real live telemetry to latest_event.json.
"""

import os
import sys
import json
import cv2
import time
from urllib.parse import quote
from dotenv import load_dotenv

from ultralytics import YOLO
from frame_queue import FrameQueueManager
from stream_grabber import MultiCameraIngestionManager
from models.anpr import LicensePlateDetector
from models.vehicle_attribute import VehicleAttributeClassifier
from pipeline import VisionPipeline
import numpy as np

# Ensure frames_cache directory exists
os.makedirs("frames_cache", exist_ok=True)

def build_rtsp_url(camera_id: str) -> str:
    load_dotenv()
    email = quote(os.getenv("SENTINEL_EMAIL", ""), safe="")
    password = quote(os.getenv("SENTINEL_RTSP_PASSWORD", ""), safe="")
    return f"rtsp://{email}:{password}@103.250.160.189:8554/stream/{camera_id}"


def get_active_cameras_config() -> list:
    """Read the user's actively selected cameras from active_cameras.json."""
    cfg_path = "active_cameras.json"
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r") as f:
                cams = json.load(f)
                if isinstance(cams, list) and len(cams) > 0:
                    return cams
        except Exception:
            pass
    return ["cam01"]


def main():
    headless_mode = "--headless" in sys.argv or os.getenv("HEADLESS", "0") == "1"
    gui_available = not headless_mode
    window_name = "Sentinel Vision AI - Tactical Command Feed"

    print("\n" + "="*65)
    print("🛡️  SENTINEL VISION AI — MASTER INTELLIGENCE ENGINE")
    print("="*65)
    print(f"Execution Mode: {'Headless Web Server Relay' if headless_mode else 'OpenCV Desktop GUI'}")
    print("="*65 + "\n")

    # 1. Instantiate AI models
    print("🧠 Loading Layer 1 Base Detector (YOLOv8)...")
    base_detector = YOLO("checkpoints/yolov8n.pt", task="detect")
    
    print("🧠 Loading Layer 2 ALPR & Vehicle Attribute Models...")
    alpr_model = LicensePlateDetector(model_weights="checkpoints/license-plate-finetune-v1n.onnx", conf_thresh=0.4)
    vehicle_attr_model = VehicleAttributeClassifier()

    # 2. Instantiate Processing Pipeline (8 Capabilities)
    pipeline = VisionPipeline(
        base_yolo=base_detector,
        alpr_model=alpr_model,
        vehicle_attr_model=vehicle_attr_model
    )

    # 3. OpenCV Window setup if not in headless mode
    if gui_available:
        try:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        except cv2.error:
            gui_available = False

    # 4. In-Memory Queue Manager & Multi-Camera Ingestion
    print("🚀 Initializing Multi-Camera Queue Manager & Stream Grabbers...")
    queue_mgr = FrameQueueManager(maxsize=120)
    multi_cam_mgr = MultiCameraIngestionManager(queue_manager=queue_mgr)

    # Initial active camera subscription
    current_active_cams = get_active_cameras_config()
    for cid in current_active_cams:
        rtsp_url = build_rtsp_url(cid)
        multi_cam_mgr.add_camera(camera_id=cid, rtsp_url=rtsp_url, target_fps=15.0)

    last_config_check = time.time()
    frame_count = 0
    latest_tiles = {}
    tile_w, tile_h = 640, 360

    print(f"✅ Ingesting real RTSP data for active camera(s): {current_active_cams}\n")

    try:
        while True:
            # Check for dynamic active camera updates every 2 seconds
            now = time.time()
            if now - last_config_check > 2.0:
                last_config_check = now
                desired_cams = get_active_cameras_config()
                if set(desired_cams) != set(current_active_cams):
                    print(f"🔄 Dynamic Camera Reconfiguration: {current_active_cams} -> {desired_cams}")
                    # Add newly checked cameras
                    for cid in desired_cams:
                        if cid not in current_active_cams:
                            multi_cam_mgr.add_camera(cid, build_rtsp_url(cid), target_fps=15.0)
                    # Remove unchecked cameras
                    for cid in current_active_cams:
                        if cid not in desired_cams:
                            multi_cam_mgr.remove_camera(cid)
                    current_active_cams = desired_cams

            # Pop next frame from queue
            frame_obj = queue_mgr.pop(timeout=0.03)
            if not frame_obj:
                time.sleep(0.005)
                continue

            # Run 8-capability cascade inference
            annotated_frame, metadata = pipeline.process_frame_object(frame_obj)
            cid = frame_obj.camera_id

            # Save real annotated frame to disk cache for live web streaming
            cache_path = f"frames_cache/{cid}.jpg"
            cv2.imwrite(cache_path, annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            # Also write default stream
            cv2.imwrite("frames_cache/latest.jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

            # Export real metadata to latest_event.json
            frame_count += 1
            if frame_count % 5 == 0:
                try:
                    with open("latest_event.json", "w") as f:
                        json.dump(metadata, f, indent=2)
                except Exception:
                    pass

            # Optional OpenCV Window if run directly without --headless
            if gui_available:
                resized = cv2.resize(annotated_frame, (tile_w, tile_h))
                latest_tiles[cid] = resized
                tiles = [latest_tiles[c] for c in current_active_cams if c in latest_tiles]
                if len(tiles) == 1:
                    display = tiles[0]
                elif len(tiles) == 2:
                    display = np.hstack([tiles[0], tiles[1]])
                else:
                    display = tiles[0]

                cv2.imshow(window_name, display)
                if cv2.waitKey(1) & 0xFF in [ord('q'), 27]:
                    break

    except KeyboardInterrupt:
        print("\n🛑 Shutting down stream grabbers...")
    finally:
        multi_cam_mgr.stop_all()
        if gui_available:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()