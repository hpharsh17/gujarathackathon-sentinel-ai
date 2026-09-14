"""
Sentinel Vision AI - Multi-Camera Stream Grabber Architecture
Runs lightweight ingestion workers across multiple RTSP streams simultaneously,
pushing standardized video frames into the centralized FrameQueueManager.
"""

import time
import threading
from typing import List, Dict
from data_access import CameraReader
from frame_queue import FrameQueueManager, QueuedFrame


class StreamGrabberWorker:
    """Individual worker dedicated to one camera feed."""
    def __init__(self, camera_id: str, rtsp_url: str, queue_manager: FrameQueueManager, target_fps: float = 15.0):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.queue = queue_manager
        self.target_fps = target_fps
        self.frame_interval = 1.0 / max(target_fps, 1.0)
        
        self.is_running = False
        self._thread = None
        self.reader = None
        self.frames_grabbed = 0

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"Grabber-{self.camera_id}")
        self._thread.start()

    def _run(self):
        print(f"📡 [StreamGrabber] Connecting to {self.camera_id}...")
        try:
            self.reader = CameraReader(camera_id=self.camera_id, rtsp_url=self.rtsp_url)
            print(f"✅ [StreamGrabber] {self.camera_id} connected successfully!")
        except Exception as e:
            print(f"❌ [StreamGrabber] Error connecting to {self.camera_id}: {e}")
            self.is_running = False
            return

        last_grab_time = 0.0

        while self.is_running:
            now = time.time()
            if now - last_grab_time < self.frame_interval:
                time.sleep(0.002)
                continue

            frame_obj = self.reader.get_next_frame()
            if frame_obj is None:
                time.sleep(0.01)
                continue

            last_grab_time = now
            self.frames_grabbed += 1

            queued = QueuedFrame(
                camera_id=frame_obj.camera_id,
                image=frame_obj.image,
                pts_ms=frame_obj.pts_ms,
                system_timestamp=frame_obj.system_timestamp,
                metadata={}
            )
            self.queue.push(queued)

    def stop(self):
        self.is_running = False
        if self.reader:
            self.reader.close()
        if self._thread:
            self._thread.join(timeout=1.0)


class MultiCameraIngestionManager:
    """
    Coordinates and monitors multiple StreamGrabber workers.
    Enables scaling from 1 camera to 50+ cameras simultaneously.
    """
    def __init__(self, queue_manager: FrameQueueManager):
        self.queue = queue_manager
        self.workers: Dict[str, StreamGrabberWorker] = {}

    def add_camera(self, camera_id: str, rtsp_url: str, target_fps: float = 15.0):
        """Registers and starts a new camera grabber."""
        if camera_id in self.workers:
            print(f"⚠️ [MultiCamera] Camera {camera_id} is already registered.")
            return

        worker = StreamGrabberWorker(camera_id, rtsp_url, self.queue, target_fps=target_fps)
        self.workers[camera_id] = worker
        worker.start()

    def remove_camera(self, camera_id: str):
        """Stops and unregisters a camera grabber."""
        if camera_id in self.workers:
            self.workers[camera_id].stop()
            del self.workers[camera_id]

    def stop_all(self):
        """Gracefully halts all active stream grabbers."""
        print("🛑 [MultiCamera] Stopping all stream grabber workers...")
        for worker in self.workers.values():
            worker.stop()
        self.workers.clear()

    def get_status(self) -> dict:
        """Returns health and status of all camera workers."""
        return {
            cid: {
                "active": w.is_running,
                "frames_grabbed": w.frames_grabbed,
                "target_fps": w.target_fps
            }
            for cid, w in self.workers.items()
        }
