"""Low-cost accident candidate detection from existing vehicle tracks."""

import math
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional


class AccidentDetector:
    """Use track motion and spatial overlap to find persistent crash candidates."""

    def __init__(self, confirmation_frames: int = 3, cooldown_seconds: float = 60.0):
        self.histories: Dict[str, deque] = defaultdict(lambda: deque(maxlen=6))
        self.candidates: Dict[str, int] = defaultdict(int)
        self.last_alert_at: Dict[str, float] = {}
        self.active_candidate: Dict[str, str] = {}
        self.confirmation_frames = confirmation_frames
        self.cooldown_seconds = cooldown_seconds

    @staticmethod
    def _center(box: List[int]) -> tuple:
        x1, y1, x2, y2 = box
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    @staticmethod
    def _iou(first: List[int], second: List[int]) -> float:
        x1 = max(first[0], second[0])
        y1 = max(first[1], second[1])
        x2 = min(first[2], second[2])
        y2 = min(first[3], second[3])
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        first_area = max(0, first[2] - first[0]) * max(0, first[3] - first[1])
        second_area = max(0, second[2] - second[0]) * max(0, second[3] - second[1])
        return intersection / max(first_area + second_area - intersection, 1)

    def update(self, camera_id: str, vehicles: List[dict], now: Optional[float] = None) -> Optional[dict]:
        now = now or time.time()
        current_ids = set()
        speeds = {}
        abrupt_tracks = set()

        for vehicle in vehicles:
            track_id = vehicle.get("track_id")
            box = vehicle.get("bounding_box")
            if track_id is None or not box:
                continue
            key = f"{camera_id}:{track_id}"
            current_ids.add(key)
            center = self._center(box)
            history = self.histories[key]
            if history:
                old_center, old_time, old_speed = history[-1]
                elapsed = max(now - old_time, 0.001)
                speed = math.dist(center, old_center) / elapsed
                if old_speed > 40.0 and speed < old_speed * 0.35:
                    abrupt_tracks.add(key)
            else:
                speed = 0.0
            speeds[key] = speed
            history.append((center, now, speed))

        possible_pairs = []
        vehicle_items = [vehicle for vehicle in vehicles if vehicle.get("track_id") is not None]
        for index, first in enumerate(vehicle_items):
            for second in vehicle_items[index + 1:]:
                if self._iou(first["bounding_box"], second["bounding_box"]) > 0.08:
                    possible_pairs.append((first["track_id"], second["track_id"]))

        stopped_tracks = {track_id for track_id, speed in speeds.items() if speed < 8.0}
        involved_tracks = set(abrupt_tracks)
        for first_id, second_id in possible_pairs:
            first_key = f"{camera_id}:{first_id}"
            second_key = f"{camera_id}:{second_id}"
            if first_key in abrupt_tracks or second_key in abrupt_tracks:
                involved_tracks.update((first_key, second_key))

        candidate_key = None
        if abrupt_tracks and (possible_pairs or len(stopped_tracks) >= 2):
            candidate_key = f"{camera_id}:" + ",".join(sorted(involved_tracks))
            self.active_candidate[camera_id] = candidate_key
        elif camera_id in self.active_candidate and (possible_pairs or len(stopped_tracks) >= 2):
            candidate_key = self.active_candidate[camera_id]
            involved_tracks = set(candidate_key.split(":", 1)[1].split(","))

        if candidate_key:
            self.candidates[candidate_key] += 1
            if self.candidates[candidate_key] >= self.confirmation_frames:
                last_alert = self.last_alert_at.get(candidate_key, 0.0)
                if now - last_alert >= self.cooldown_seconds:
                    self.last_alert_at[candidate_key] = now
                    return {
                        "type": "ACCIDENT_CANDIDATE",
                        "severity": "HIGH",
                        "camera_id": camera_id,
                        "track_ids": sorted(involved_tracks),
                        "reason": "abrupt vehicle deceleration with collision or stop pattern",
                        "confirmed_frames": self.candidates[candidate_key],
                        "detected_at": now,
                    }

        for candidate_key in list(self.candidates):
            if candidate_key.startswith(f"{camera_id}:") and not any(track_id in candidate_key for track_id in current_ids):
                del self.candidates[candidate_key]
        return None