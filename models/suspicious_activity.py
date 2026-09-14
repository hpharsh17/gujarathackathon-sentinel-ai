"""
Suspicious Activity, Intrusion & Abandoned Object Detection Module (Capability 5 & 6)
Monitors human behavior (running, loitering, zone intrusion) and tracks unattended objects.
"""

import time
import math
from typing import List, Dict
from shapely.geometry import Point, Polygon


class BehaviorAndObjectTracker:
    """
    Analyzes spatial-temporal behavior of tracked persons and stationary objects.
    Decoupled from model inference - operates on bounding box tracks for zero GPU overhead.
    """
    def __init__(self, restricted_zone: list = None, loiter_seconds: float = 30.0, abandoned_seconds: float = 30.0):
        # Default zone (e.g. middle of road / restricted area)
        if restricted_zone is None:
            restricted_zone = [(200, 200), (800, 200), (800, 700), (200, 700)]
        self.zone = Polygon(restricted_zone)
        
        self.loiter_seconds = loiter_seconds
        self.abandoned_seconds = abandoned_seconds

        # Track history: track_id -> {"first_seen": t, "last_seen": t, "positions": [(x, y, t)], "type": str}
        self.person_tracks: Dict[int, dict] = {}
        self.object_tracks: Dict[str, dict] = {}

    def update_person(self, track_id: int, box: list) -> List[dict]:
        """
        Updates a tracked person and returns any detected suspicious behavior events.
        """
        now = time.time()
        x1, y1, x2, y2 = box
        cx, cy = (x1 + x2) // 2, y2  # Base/feet of person
        alerts = []

        if track_id not in self.person_tracks:
            self.person_tracks[track_id] = {
                "first_seen": now,
                "last_seen": now,
                "positions": [(cx, cy, now)],
                "alerts_sent": set()
            }
        else:
            p_data = self.person_tracks[track_id]
            p_data["last_seen"] = now
            p_data["positions"].append((cx, cy, now))
            
            # Keep last 15 position points
            if len(p_data["positions"]) > 15:
                p_data["positions"].pop(0)

            # 1. Check Running / High Velocity
            if len(p_data["positions"]) >= 4:
                old_x, old_y, old_t = p_data["positions"][0]
                dist = math.sqrt((cx - old_x)**2 + (cy - old_y)**2)
                dt = max(now - old_t, 0.001)
                speed_px_sec = dist / dt

                if speed_px_sec > 180.0 and "RUNNING" not in p_data["alerts_sent"]:
                    p_data["alerts_sent"].add("RUNNING")
                    alerts.append({
                        "type": "SUSPICIOUS_RUNNING",
                        "track_id": track_id,
                        "speed_px_s": round(speed_px_sec, 1),
                        "box": box
                    })

            # 2. Check Loitering (Stationary in scene > threshold)
            dwelling_time = now - p_data["first_seen"]
            if dwelling_time > self.loiter_seconds and "LOITERING" not in p_data["alerts_sent"]:
                p_data["alerts_sent"].add("LOITERING")
                alerts.append({
                    "type": "LOITERING_DETECTED",
                    "track_id": track_id,
                    "dwelling_sec": round(dwelling_time, 1),
                    "box": box
                })

            # 3. Check Restricted Zone Intrusion
            foot = Point(cx, cy)
            if self.zone.contains(foot) and "INTRUSION" not in p_data["alerts_sent"]:
                p_data["alerts_sent"].add("INTRUSION")
                alerts.append({
                    "type": "ZONE_INTRUSION",
                    "track_id": track_id,
                    "box": box
                })

        return alerts

    def update_object(self, obj_id: str, box: list, obj_class: str, nearby_persons: List[list]) -> List[dict]:
        """
        Tracks unattended objects (backpacks, suitcases).
        Triggers alert if stationary without any person nearby for > abandoned_seconds.
        """
        now = time.time()
        x1, y1, x2, y2 = box
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        alerts = []

        # Check if any person is within 100 pixels of the object
        person_nearby = False
        for p_box in nearby_persons:
            px1, py1, px2, py2 = p_box
            pcx, pcy = (px1 + px2) // 2, (py1 + py2) // 2
            if math.sqrt((cx - pcx)**2 + (cy - pcy)**2) < 120:
                person_nearby = True
                break

        if obj_id not in self.object_tracks:
            self.object_tracks[obj_id] = {
                "first_seen": now,
                "stationary_since": now if not person_nearby else None,
                "class": obj_class,
                "box": box,
                "alerted": False
            }
        else:
            o_data = self.object_tracks[obj_id]
            o_data["box"] = box

            if person_nearby:
                # Owner returned; reset timer
                o_data["stationary_since"] = None
                o_data["alerted"] = False
            else:
                if o_data["stationary_since"] is None:
                    o_data["stationary_since"] = now
                else:
                    duration = now - o_data["stationary_since"]
                    if duration >= self.abandoned_seconds and not o_data["alerted"]:
                        o_data["alerted"] = True
                        alerts.append({
                            "type": "ABANDONED_OBJECT_ALERT",
                            "object_type": obj_class,
                            "stationary_seconds": round(duration, 1),
                            "box": box
                        })

        return alerts

    def cleanup_stale_tracks(self, max_idle: float = 5.0):
        """Cleans up tracks that have left the scene."""
        now = time.time()
        self.person_tracks = {tid: data for tid, data in self.person_tracks.items() if now - data["last_seen"] < max_idle}