"""
License Plate Recognition (ALPR) Module
Responsible for detecting vehicle plates and running OCR on crops.
"""

import torch
from ultralytics import YOLO
import easyocr


class LicensePlateDetector:
    def __init__(self, model_weights: str = "yolov8n.pt", conf_thresh: float = 0.4):
        self.conf_thresh = conf_thresh
        
        # Dynamically check for GPU
        self.use_gpu = torch.cuda.is_available()
        # YOLO prefers '0' for cuda device 0, or 'cpu'
        self.device = '0' if self.use_gpu else 'cpu'
        
        print(f"[{'GPU' if self.use_gpu else 'CPU'}] Initializing YOLO ALPR on {self.device}...")
        self.detector = YOLO(model_weights, task="detect")
        # Removed .to(device) because ONNX models handle device selection during inference
        
        print(f"[{'GPU' if self.use_gpu else 'CPU'}] Initializing EasyOCR on {self.device}...")
        self.ocr_reader = easyocr.Reader(['en'], gpu=self.use_gpu)

    def detect(self, image):
        """
        Detects vehicle bounding boxes and runs OCR on crops.
        Returns a list of detected plates with text and coordinates.
        """
        # Pass the device argument directly during prediction for ONNX models
        results = self.detector(image, verbose=False, device=self.device)
        detected_plates = []

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf >= self.conf_thresh:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cropped_region = image[y1:y2, x1:x2]

                    if cropped_region.size > 0:
                        ocr_res = self.ocr_reader.readtext(cropped_region)
                        plate_text = " ".join([res[1] for res in ocr_res]).strip()

                        if plate_text:
                            detected_plates.append({
                                "bounding_box": [x1, y1, x2, y2],
                                "confidence": round(conf, 2),
                                "extracted_text": plate_text
                            })

        return detected_plates