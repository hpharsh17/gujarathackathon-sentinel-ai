"""
Vehicle Attribute Classifier (Capability 4)
Classifies Indian vehicle body type (via UVH YOLOv11 mapping) and dominant exterior color (via HSV analysis).
"""

import cv2
import numpy as np


class VehicleAttributeClassifier:
    def __init__(self):
        # 14 Indian vehicle classes matching checkpoints/UVH-26-MV-YOLOv11-S.pt
        self.vehicle_classes = {
            0: "Hatchback",
            1: "Sedan",
            2: "SUV",
            3: "MUV",
            4: "Bus",
            5: "Truck",
            6: "Three-wheeler",
            7: "Two-wheeler",
            8: "LCV",
            9: "Mini-bus",
            10: "tempo-traveller",
            11: "bicycle",
            12: "Van",
            13: "Others",
        }

    def get_vehicle_type(self, class_id: int) -> str:
        """Translate class ID to Indian vehicle category."""
        return self.vehicle_classes.get(class_id, "Vehicle")

    def extract_color(self, crop: np.ndarray) -> str:
        """
        Fast, robust dominant color extraction from vehicle crop.
        Analyzes the central 50% region of the vehicle to avoid asphalt/tires.
        """
        if crop is None or crop.size == 0:
            return "Unknown"

        h, w = crop.shape[:2]
        if h < 20 or w < 20:
            return "Unknown"

        # Crop center 50% (avoids background roads and black tires)
        ch1, ch2 = int(h * 0.25), int(h * 0.75)
        cw1, cw2 = int(w * 0.25), int(w * 0.75)
        body_crop = crop[ch1:ch2, cw1:cw2]

        if body_crop.size == 0:
            return "Unknown"

        hsv = cv2.cvtColor(body_crop, cv2.COLOR_BGR2HSV)
        h_channel = hsv[:, :, 0]
        s_channel = hsv[:, :, 1]
        v_channel = hsv[:, :, 2]

        mean_s = np.mean(s_channel)
        mean_v = np.mean(v_channel)

        # Grayscale detection (low saturation)
        if mean_s < 40:
            if mean_v < 60:
                return "Black"
            elif mean_v > 180:
                return "White"
            else:
                return "Silver/Grey"

        # Saturated colors (hue analysis)
        mean_h = np.mean(h_channel)
        if mean_h < 10 or mean_h > 165:
            return "Red"
        elif 10 <= mean_h < 25:
            return "Orange"
        elif 25 <= mean_h < 35:
            return "Yellow"
        elif 35 <= mean_h < 85:
            return "Green"
        elif 85 <= mean_h < 135:
            return "Blue"
        else:
            return "Other"

    def analyze(self, crop: np.ndarray, class_id: int = None) -> dict:
        """Full attribute analysis returning vehicle type and dominant color."""
        v_type = self.get_vehicle_type(class_id) if class_id is not None else "Vehicle"
        color = self.extract_color(crop)
        return {
            "type": v_type,
            "color": color
        }