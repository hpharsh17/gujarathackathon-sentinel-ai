"""CPU-only crowd anomaly detection using a fluid-flow approximation."""

import math
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional


class CrowdFlowAnomalyDetector:
    """Estimate crowd compression, vortex motion, and disordered surges from tracks."""

    def __init__(self, min_people: int = 5, history_size: int = 8, alert_cooldown: float = 12.0):
        self.min_people = min_people
        self.track_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.baselines: Dict[str, dict] = {}
        self.last_alert_at: Dict[str, float] = {}
        self.alert_cooldown = alert_cooldown

    @staticmethod
    def _stats(vectors: List[tuple]) -> tuple:
        if not vectors:
            return 0.0, 0.0
        mean_x = sum(vector[0] for vector in vectors) / len(vectors)
        mean_y = sum(vector[1] for vector in vectors) / len(vectors)
        mean_speed = sum(math.hypot(*vector) for vector in vectors) / len(vectors)
        alignment = math.hypot(mean_x, mean_y) / max(mean_speed, 0.001)
        return mean_speed, max(0.0, min(alignment, 1.0))

    def update(self, camera_id: str, people: List[dict], frame_width: int, frame_height: int, now: Optional[float] = None) -> Optional[dict]:
        now = now or time.time()
        camera_id = camera_id.lower()
        positions = {}
        for person in people:
            track_id = person.get("track_id")
            box = person.get("box")
            if track_id is None or not box:
                continue
            x1, y1, x2, y2 = box
            positions[str(track_id)] = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
        if len(positions) < self.min_people:
            return None

        velocities = []
        ordered_positions = []
        for track_id, position in positions.items():
            history = self.track_history[track_id]
            if history:
                old_x, old_y, old_time = history[-1]
                elapsed = max(now - old_time, 0.001)
                velocities.append(((position[0] - old_x) / elapsed, (position[1] - old_y) / elapsed))
            ordered_positions.append(position)
            history.append((position[0], position[1], now))

        occupied_width = max(max(p[0] for p in ordered_positions) - min(p[0] for p in ordered_positions) + 40.0, 40.0)
        occupied_height = max(max(p[1] for p in ordered_positions) - min(p[1] for p in ordered_positions) + 40.0, 40.0)
        occupied_area = min(occupied_width * occupied_height, float(frame_width * frame_height))
        density = len(ordered_positions) / max(occupied_area / 100000.0, 0.001)
        mean_speed, alignment = self._stats(velocities)
        baseline = self.baselines.setdefault(camera_id, {"density": density, "speed": mean_speed})
        if len(velocities) < self.min_people:
            return None

        baseline["density"] = baseline["density"] * 0.95 + density * 0.05
        baseline["speed"] = baseline["speed"] * 0.95 + mean_speed * 0.05
        density_ratio = density / max(baseline["density"], 0.001)
        speed_ratio = mean_speed / max(baseline["speed"], 0.001)

        divergence_values = []
        vorticity_values = []
        for index, (x_pos, y_pos) in enumerate(ordered_positions):
            nearby = []
            for other_index, (other_x, other_y) in enumerate(ordered_positions):
                if index == other_index:
                    continue
                delta_x, delta_y = other_x - x_pos, other_y - y_pos
                distance = math.hypot(delta_x, delta_y)
                if 20.0 < distance < 250.0:
                    nearby.append((delta_x, delta_y, velocities[other_index]))
            if not nearby:
                continue
            radial = []
            rotational = []
            own_velocity = velocities[index]
            for delta_x, delta_y, other_velocity in nearby:
                distance = math.hypot(delta_x, delta_y)
                unit_x, unit_y = delta_x / distance, delta_y / distance
                relative_x = other_velocity[0] - own_velocity[0]
                relative_y = other_velocity[1] - own_velocity[1]
                radial.append(relative_x * unit_x + relative_y * unit_y)
                rotational.append(relative_x * unit_y - relative_y * unit_x)
            divergence_values.append(sum(radial) / len(radial))
            vorticity_values.append(sum(abs(value) for value in rotational) / len(rotational))

        divergence = sum(divergence_values) / len(divergence_values) if divergence_values else 0.0
        vorticity = sum(vorticity_values) / len(vorticity_values) if vorticity_values else 0.0
        anomaly_type = None
        severity = "LOW"
        if divergence < -15.0 and density_ratio > 1.4:
            anomaly_type, severity = "CROWD_COMPRESSION", "HIGH"
        elif vorticity > 70.0 and alignment < 0.45:
            anomaly_type, severity = "CROWD_VORTEX", "MEDIUM"
        elif speed_ratio > 2.0 and alignment < 0.55:
            anomaly_type, severity = "DISORDERED_SURGE", "HIGH"
        if anomaly_type is None or now - self.last_alert_at.get(camera_id, 0.0) < self.alert_cooldown:
            return None

        self.last_alert_at[camera_id] = now
        return {
            "type": anomaly_type,
            "severity": severity,
            "camera_id": camera_id,
            "people_count": len(ordered_positions),
            "density": round(density, 2),
            "density_ratio": round(density_ratio, 2),
            "mean_speed_px_s": round(mean_speed, 1),
            "directional_alignment": round(alignment, 2),
            "divergence": round(divergence, 1),
            "vorticity": round(vorticity, 1),
        }

    def cleanup(self, max_idle: float = 5.0, now: Optional[float] = None):
        now = now or time.time()
        stale = [track_id for track_id, history in self.track_history.items() if not history or now - history[-1][2] > max_idle]
        for track_id in stale:
            del self.track_history[track_id]
