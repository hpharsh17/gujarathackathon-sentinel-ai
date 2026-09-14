"""Low-cost, location-aware vehicle sightings across cameras."""

import math
import threading
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional


class CrossCameraVehicleTracker:
    """Correlate confirmed plates without running another vision model."""

    def __init__(
        self,
        camera_registry: Dict[str, dict],
        max_distance_km: float = 25.0,
        max_age_seconds: float = 2 * 60 * 60,
        max_speed_kmh: float = 140.0,
        max_sightings_per_plate: int = 12,
    ):
        self.camera_registry = camera_registry
        self.max_distance_km = max_distance_km
        self.max_age_seconds = max_age_seconds
        self.max_speed_kmh = max_speed_kmh
        self.max_sightings_per_plate = max_sightings_per_plate
        self.sightings = defaultdict(lambda: deque(maxlen=max_sightings_per_plate))
        self.lock = threading.Lock()

    @staticmethod
    def normalize_plate(plate_text: str) -> str:
        return "".join(character for character in (plate_text or "").upper() if character.isalnum())

    @staticmethod
    def distance_km(first: dict, second: dict) -> Optional[float]:
        lat1, lon1 = first.get("latitude"), first.get("longitude")
        lat2, lon2 = second.get("latitude"), second.get("longitude")
        if None in (lat1, lon1, lat2, lon2):
            return None

        radius_km = 6371.0
        lat_delta = math.radians(lat2 - lat1)
        lon_delta = math.radians(lon2 - lon1)
        a = (
            math.sin(lat_delta / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(lon_delta / 2) ** 2
        )
        return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def observe(self, plate_text: str, camera_id: str, observed_at: Optional[float] = None) -> List[dict]:
        plate = self.normalize_plate(plate_text)
        camera_id = camera_id.lower()
        camera = self.camera_registry.get(camera_id, {})
        observed_at = observed_at or time.time()
        if not plate or not camera:
            return []

        current = {
            "camera_id": camera_id,
            "location_name": camera.get("location_name", "Unknown"),
            "district": camera.get("district", "Unknown"),
            "latitude": camera.get("latitude"),
            "longitude": camera.get("longitude"),
            "observed_at": observed_at,
        }

        matches = []
        with self.lock:
            previous_sightings = self.sightings[plate]
            for previous in reversed(previous_sightings):
                if previous["camera_id"] == camera_id:
                    continue

                elapsed = observed_at - previous["observed_at"]
                if elapsed <= 0 or elapsed > self.max_age_seconds:
                    continue

                distance = self.distance_km(previous, current)
                if distance is None or distance > self.max_distance_km:
                    continue

                speed = distance / (elapsed / 3600)
                if speed > self.max_speed_kmh:
                    continue

                matches.append({
                    **previous,
                    "distance_km": round(distance, 2),
                    "elapsed_seconds": round(elapsed, 1),
                    "estimated_speed_kmh": round(speed, 1),
                })

            previous_sightings.append(current)

        return matches

    def get_trail(self, plate_text: str) -> List[dict]:
        plate = self.normalize_plate(plate_text)
        with self.lock:
            return list(self.sightings.get(plate, []))

    def search_nearest(self, plate_text: str, source_camera_id: Optional[str] = None) -> dict:
        """Find the most logical next camera for a vehicle's recorded trail."""
        plate = self.normalize_plate(plate_text)
        source_camera_id = source_camera_id.lower() if source_camera_id else None
        with self.lock:
            trail = list(self.sightings.get(plate, []))

        if not trail:
            return {"plate": plate, "source_camera": source_camera_id, "nearest_camera": None, "sightings": []}

        source = self.camera_registry.get(source_camera_id) if source_camera_id else None
        if source is None:
            source = trail[-1]
            source_camera_id = source.get("camera_id")

        candidates = []
        for camera_id, camera in self.camera_registry.items():
            if camera_id == source_camera_id:
                continue
            distance = self.distance_km(source, camera)
            if distance is not None and distance <= self.max_distance_km:
                candidates.append((distance, camera_id, camera))
        candidates.sort(key=lambda item: item[0])

        next_sightings = []
        source_time = source.get("observed_at", 0.0)
        for sighting in trail:
            if sighting.get("camera_id") == source_camera_id or sighting.get("observed_at", 0.0) <= source_time:
                continue
            distance = self.distance_km(source, sighting)
            elapsed = sighting["observed_at"] - source_time
            if distance is None or elapsed <= 0 or elapsed > self.max_age_seconds:
                continue
            speed = distance / (elapsed / 3600)
            if speed <= self.max_speed_kmh:
                next_sightings.append({
                    **sighting,
                    "distance_from_source_km": round(distance, 2),
                    "elapsed_seconds": round(elapsed, 1),
                    "estimated_speed_kmh": round(speed, 1),
                })

        nearest_camera = None
        if candidates:
            distance, camera_id, camera = candidates[0]
            nearest_camera = {
                "camera_id": camera_id,
                "location_name": camera.get("location_name", "Unknown"),
                "district": camera.get("district", "Unknown"),
                "latitude": camera.get("latitude"),
                "longitude": camera.get("longitude"),
                "distance_from_source_km": round(distance, 2),
            }

        next_sightings.sort(key=lambda sighting: sighting["distance_from_source_km"])
        return {
            "plate": plate,
            "source_camera": source_camera_id,
            "nearest_camera": nearest_camera,
            "sightings": next_sightings,
        }