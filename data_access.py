import os
import cv2
import time
import numpy as np
import threading
from dataclasses import dataclass, field

# Tesseract removed - camera metadata and GIS are retrieved directly from Supabase DB


@dataclass
class CameraMetadata:
    """Static metadata for a single camera feed."""
    camera_id: str
    width: int
    height: int
    fps: float
    codec: str
    source_url: str = field(repr=False)


@dataclass
class CameraFrame:
    """Standardized representation of a single video frame with metadata."""
    camera_id: str
    image: np.ndarray
    pts_ms: float
    system_timestamp: float = field(default_factory=time.time)
    ocr_data: dict = field(default_factory=dict)


class CameraReader:
    """
    Unified Data-Access Layer for Sentinel RTSP streams.
    Now utilizes a Background Thread to continuously drain the RTSP buffer
    so the UI never hangs and the AI can take as long as it needs.
    """
    def __init__(self, camera_id: str, rtsp_url: str):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        
        # Prevent Macroblock drop errors by forcing TCP, increasing buffer size, and allowing delay
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|buffer_size;10240000|max_delay;5000000"
        self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        
        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to connect to camera {self.camera_id}")
            
        # Extract Codec Dynamically using FourCC
        fourcc = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        codec_name = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]) if fourcc else "UNKNOWN"
        if not codec_name.strip() or codec_name == "UNKNOWN":
            codec_name = "h264"

        self.metadata = CameraMetadata(
            camera_id=self.camera_id,
            width=int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=self._cap.get(cv2.CAP_PROP_FPS),
            codec=codec_name, 
            source_url=self.rtsp_url
        )

        # THREADING SETUP: Start the background frame grabber
        self.latest_frame = None
        self.latest_pts = 0.0
        self.is_running = True
        
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        
        # Wait until the first frame is grabbed before returning control
        while self.latest_frame is None and self.is_running:
            time.sleep(0.01)

    def _update_loop(self):
        """
        Background thread that continually pulls frames from OpenCV.
        This completely eliminates the RTSP buffer freezing issue.
        """
        while self.is_running:
            ok, frame = self._cap.read()
            if not ok:
                self.is_running = False
                break
            
            self.latest_frame = frame
            self.latest_pts = self._cap.get(cv2.CAP_PROP_POS_MSEC)
            
            # Tiny sleep to yield thread control slightly, keeps CPU happy
            time.sleep(0.005)

    def get_next_frame(self) -> CameraFrame | None:
        """Instantly grabs the newest frame from the background thread."""
        if not self.is_running or self.latest_frame is None:
            return None
            
        # Use .copy() so downstream consumers don't mutate thread memory
        frame = self.latest_frame.copy()
        pts_ms = self.latest_pts

        return CameraFrame(
            camera_id=self.camera_id,
            image=frame,
            pts_ms=pts_ms,
            ocr_data={}
        )

    def close(self):
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
        self._cap.release()
