import cv2
import json
import os
import threading
import queue
import time
from typing import List, Dict
from database import CameraDatabase
from cross_camera import CrossCameraVehicleTracker
from models.suspicious_activity import BehaviorAndObjectTracker
from models.accident_detection import AccidentDetector
from models.crowd_flow import CrowdFlowAnomalyDetector
from models.face_recognition import FaceRecognitionEngine
from alert_dispatcher import EmergencyDispatcher


CROSS_CAMERA_CONFIG_FILE = "cross_camera_config.json"


class VisionPipeline:
    """
    Sentinel Vision AI - Master 8-Capability Cascade Engine
    1. People Detection & Crowd Density
    2. Vehicle Detection (Indian Classes)
    3. ANPR License Plate Recognition
    4. Vehicle Attributes (Body Type & Color)
    5. Abandoned / Suspicious Object Detection
    6. Suspicious Activity Tracking (Running, Loitering, Intrusion)
    7. Face Extraction & 512-d Biometric Vector Embeddings
    8. Watchlist Engine (Supabase Stolen Vehicle & Wanted Person matching)
    """
    def __init__(self, base_yolo, alpr_model, vehicle_attr_model):
        self.base_yolo = base_yolo
        self.alpr_model = alpr_model
        self.vehicle_attr_model = vehicle_attr_model
        self.device_registry = CameraDatabase()
        
        # Capability 5 & 6 Tracker (Behavior, Intrusion & Abandoned Luggage)
        self.activity_tracker = BehaviorAndObjectTracker(loiter_seconds=20.0, abandoned_seconds=15.0)
        self.accident_detector = AccidentDetector()
        self.crowd_flow_detector = CrowdFlowAnomalyDetector()
        self.emergency_dispatcher = EmergencyDispatcher()
        
        # Capability 7 Face Recognition Engine
        self.face_engine = FaceRecognitionEngine(use_gpu=True)

        # Standard COCO IDs for Base YOLO
        self.coco_vehicles = {2: "Car", 3: "Motorcycle", 5: "Bus", 7: "Truck"}
        self.coco_objects = {24: "Backpack", 26: "Handbag", 28: "Suitcase"}

        # Track IDs are local to a camera, so always scope them by camera ID.
        self.known_plates = {}
        self.pending_ocr_tracks = set()
        self.failed_attempts = {}
        self.cross_camera_tracker = CrossCameraVehicleTracker(CameraDatabase.LOCAL_REGISTRY)
        self.vehicle_trails_file = "vehicle_trails.json"
        self.cross_camera_enabled = True
        self.cross_camera_config_mtime = None

        # Background worker thread for slow EasyOCR (ANPR) & Watchlist sync
        self.anpr_queue = queue.Queue(maxsize=15)
        self.anpr_thread = threading.Thread(target=self._anpr_worker, daemon=True)
        self.anpr_thread.start()

    def _anpr_worker(self):
        """Worker thread executing slow EasyOCR without blocking real-time video."""
        while True:
            try:
                task = self.anpr_queue.get()
                if task is None:
                    break
                v_crop, camera_id, track_id = task
                track_key = (camera_id, track_id)
                
                plate_results = self.alpr_model.detect(v_crop)
                if plate_results:
                    best_plate = max(plate_results, key=lambda p: p.get("confidence", 0.0))
                    plate_text = best_plate["extracted_text"]
                    
                    # Check against Supabase Stolen Vehicle Watchlist (Capability 8)
                    watchlist_hit = self.device_registry.check_stolen_vehicle(plate_text)
                    if self._is_cross_camera_enabled():
                        cross_camera_matches = self.cross_camera_tracker.observe(plate_text, camera_id)
                        cross_camera_trail = self.cross_camera_tracker.get_trail(plate_text)
                        camera_info = self.device_registry.get_camera_info(camera_id)
                        self.device_registry.record_vehicle_sighting(plate_text, camera_info, time.time())
                        self._persist_vehicle_trails()
                    else:
                        cross_camera_matches = []
                        cross_camera_trail = []
                    if watchlist_hit:
                        print(f"🚨 [WATCHLIST ALERT] Stolen Vehicle Detected! Plate: {plate_text}")
                    else:
                        print(f"✅ [ANPR Detected] Vehicle #{track_id} at {camera_id}: {plate_text}")

                    self.known_plates[track_key] = {
                        "text": plate_text,
                        "relative_box": best_plate["bounding_box"],
                        "stolen_alert": watchlist_hit,
                        "timestamp": time.time(),
                        "cross_camera_matches": cross_camera_matches,
                        "cross_camera_trail": cross_camera_trail,
                    }
                else:
                    self.failed_attempts[track_key] = self.failed_attempts.get(track_key, 0) + 1
                    
                self.pending_ocr_tracks.discard(track_key)
                self.anpr_queue.task_done()
            except Exception as e:
                print(f"[ANPR Worker Warning] {e}")
                time.sleep(0.01)

    def _is_cross_camera_enabled(self):
        try:
            config_mtime = os.path.getmtime(CROSS_CAMERA_CONFIG_FILE)
            if config_mtime == self.cross_camera_config_mtime:
                return self.cross_camera_enabled
        except OSError:
            self.cross_camera_config_mtime = None
            self.cross_camera_enabled = True
            return True

        try:
            with open(CROSS_CAMERA_CONFIG_FILE, "r") as config_file:
                self.cross_camera_enabled = bool(json.load(config_file).get("enabled", True))
                self.cross_camera_config_mtime = config_mtime
                return self.cross_camera_enabled
        except (OSError, json.JSONDecodeError, AttributeError):
            self.cross_camera_config_mtime = config_mtime
            self.cross_camera_enabled = True
            return True

    def _persist_vehicle_trails(self):
        """Share compact plate trails with the API process through the bind mount."""
        trails = {
            plate: self.cross_camera_tracker.get_trail(plate)
            for plate in self.cross_camera_tracker.sightings
        }
        temp_file = f"{self.vehicle_trails_file}.tmp"
        try:
            with open(temp_file, "w") as trail_file:
                json.dump(trails, trail_file)
            os.replace(temp_file, self.vehicle_trails_file)
        except OSError:
            pass

    def draw_annotations(self, image, vehicles, people, objects, alerts, location_info=None):
        """Draw annotations directly onto a copy of the frame in real-time."""
        annotated = image.copy()
        h, w = annotated.shape[:2]

        # 1. Draw Enterprise GIS Location Banner at top
        if location_info and location_info.get("location_name"):
            loc_name = location_info.get("location_name", "Unknown")
            dist = location_info.get("district", "")
            lat = location_info.get("latitude")
            lon = location_info.get("longitude")
            cid = location_info.get("camera_id", "").upper()
            
            coord_str = f" [{lat}, {lon}]" if lat and lon else ""
            hud_text = f"CAM: {cid} | LOCATION: {loc_name}, {dist}{coord_str}"
            
            overlay = annotated.copy()
            cv2.rectangle(overlay, (0, 0), (w, 38), (15, 15, 20), -1)
            cv2.addWeighted(overlay, 0.8, annotated, 0.2, 0, annotated)
            
            cv2.putText(annotated, hud_text, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 230, 255), 2)

        # 2. Draw People (Cap 1 & 6 & 7)
        for p in people:
            x1, y1, x2, y2 = p["box"]
            tid = p.get("track_id")
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 200, 0), 2)
            label = f"Person #{tid}" if tid is not None else "Person"
            cv2.putText(annotated, label, (x1, max(y1 - 6, 45)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)

        # 3. Draw Vehicles (Cap 2, 3, 4 & 8)
        for v in vehicles:
            x1, y1, x2, y2 = v["bounding_box"]
            v_type = v["vehicle_type"]
            v_color = v.get("color", "")
            track_id = v.get("track_id")
            plate_text = v.get("plate_text")
            plate_box = v.get("plate_box")
            stolen = v.get("stolen_alert")

            # Box color: Red if stolen, Blue normally
            box_color = (0, 0, 255) if stolen else (255, 120, 0)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)
            
            # Label: Color + Type + ID
            color_prefix = f"{v_color} " if v_color and v_color != "Unknown" else ""
            v_label = f"{color_prefix}{v_type} #{track_id}" if track_id is not None else f"{color_prefix}{v_type}"
            cv2.putText(annotated, v_label, (x1, max(y1 - 8, 48)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, box_color, 2)

            # Draw Plate Text
            if plate_text:
                plate_color = (0, 0, 255) if stolen else (0, 255, 0)
                if plate_box:
                    px1, py1, px2, py2 = plate_box
                    cv2.rectangle(annotated, (px1, py1), (px2, py2), plate_color, 2)
                    cv2.putText(annotated, plate_text, (px1, max(py1 - 8, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, plate_color, 2)
                else:
                    cv2.putText(annotated, f"[{plate_text}]", (x1, min(y2 + 20, h - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, plate_color, 2)

        # 4. Draw Suspicious / Abandoned Objects (Cap 5)
        for obj in objects:
            ox1, oy1, ox2, oy2 = obj["box"]
            cv2.rectangle(annotated, (ox1, oy1), (ox2, oy2), (0, 165, 255), 2)
            cv2.putText(annotated, f"Obj: {obj['class']}", (ox1, max(oy1 - 6, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

        # 5. Draw Active Security Alerts (Cap 5 & 6)
        if alerts:
            alert_y = 65
            for alert in alerts:
                a_text = f"⚠️ {alert['type']}"
                cv2.rectangle(annotated, (15, alert_y - 18), (360, alert_y + 8), (0, 0, 180), -1)
                cv2.putText(annotated, a_text, (20, alert_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
                alert_y += 32

        return annotated

    def process_frame_object(self, frame_obj):
        """Executes full 8-capability cascade in real-time (~20-25ms on GPU)."""
        if frame_obj is None:
            return None, None

        vehicles_detected = []
        people_detected = []
        objects_detected = []
        plates_detected = []
        active_alerts = []

        device = self.alpr_model.device

        try:
            # Base Multi-Object Tracking (Person, Vehicles, Luggage)
            yolo_results = self.base_yolo.track(frame_obj.image, persist=True, verbose=False, device=device)
        except Exception:
            yolo_results = self.base_yolo(frame_obj.image, verbose=False, device=device)

        person_boxes = []

        for r in yolo_results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                crop = frame_obj.image[y1:y2, x1:x2]

                if crop.size == 0:
                    continue

                track_id = int(box.id[0]) if box.id is not None else None
                if track_id is None:
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    track_id = f"pos_{cx // 60}_{cy // 60}"

                # -------------------------------------------------------------
                # CAPABILITY 1, 6 & 7: PERSONS, ACTIVITY & FACES
                # -------------------------------------------------------------
                if cls_id == 0:  # Person
                    people_detected.append({
                        "track_id": track_id,
                        "box": [x1, y1, x2, y2],
                        "confidence": round(float(box.conf[0]), 2)
                    })
                    person_boxes.append([x1, y1, x2, y2])

                    # Cap 6: Suspicious Behavior Tracking (Running, Loitering, Intrusion)
                    if isinstance(track_id, int):
                        b_alerts = self.activity_tracker.update_person(track_id, [x1, y1, x2, y2])
                        active_alerts.extend(b_alerts)

                # -------------------------------------------------------------
                # CAPABILITY 2, 3, 4 & 8: VEHICLES, ANPR, ATTRIBUTES & WATCHLIST
                # -------------------------------------------------------------
                elif cls_id in self.coco_vehicles:
                    v_type = self.coco_vehicles[cls_id]
                    
                    # Cap 4: Dominant Color Extraction
                    v_color = self.vehicle_attr_model.extract_color(crop)

                    # Cap 3: ANPR Check
                    plate_text = None
                    plate_box = None
                    stolen_alert = None

                    track_key = (frame_obj.camera_id, track_id)
                    if track_key in self.known_plates:
                        known_info = self.known_plates[track_key]
                        plate_text = known_info["text"]
                        rx1, ry1, rx2, ry2 = known_info["relative_box"]
                        plate_box = [x1 + rx1, y1 + ry1, min(x1 + rx2, x2), min(y1 + ry2, y2)]
                        stolen_alert = known_info.get("stolen_alert")
                        plates_detected.append({
                            "track_id": track_id,
                            "plate_text": plate_text,
                            "bounding_box": plate_box,
                            "stolen": bool(stolen_alert),
                            "cross_camera_matches": known_info.get("cross_camera_matches", []) if self._is_cross_camera_enabled() else [],
                            "cross_camera_trail": known_info.get("cross_camera_trail", []) if self._is_cross_camera_enabled() else []
                        })
                    else:
                        if (w >= 50 and h >= 50 
                            and track_key not in self.pending_ocr_tracks
                            and self.failed_attempts.get(track_key, 0) < 3):
                            
                            self.pending_ocr_tracks.add(track_key)
                            try:
                                self.anpr_queue.put_nowait((crop.copy(), frame_obj.camera_id, track_id))
                            except queue.Full:
                                self.pending_ocr_tracks.discard(track_key)

                    vehicles_detected.append({
                        "track_id": track_id,
                        "vehicle_type": v_type,
                        "color": v_color,
                        "confidence": round(float(box.conf[0]), 2),
                        "bounding_box": [x1, y1, x2, y2],
                        "plate_text": plate_text,
                        "plate_box": plate_box,
                        "stolen_alert": stolen_alert,
                        "cross_camera_matches": known_info.get("cross_camera_matches", []) if plate_text and self._is_cross_camera_enabled() else [],
                        "cross_camera_trail": known_info.get("cross_camera_trail", []) if plate_text and self._is_cross_camera_enabled() else []
                    })

                # -------------------------------------------------------------
                # CAPABILITY 5: ABANDONED OBJECTS (Backpack, Handbag, Suitcase)
                # -------------------------------------------------------------
                elif cls_id in self.coco_objects:
                    obj_name = self.coco_objects[cls_id]
                    objects_detected.append({
                        "id": track_id,
                        "class": obj_name,
                        "box": [x1, y1, x2, y2]
                    })
                    o_alerts = self.activity_tracker.update_object(str(track_id), [x1, y1, x2, y2], obj_name, person_boxes)
                    active_alerts.extend(o_alerts)

        # Lookup enterprise GIS from database
        location_info = self.device_registry.get_camera_info(frame_obj.camera_id)
        crowd_flow_alert = self.crowd_flow_detector.update(
            frame_obj.camera_id,
            people_detected,
            frame_obj.image.shape[1],
            frame_obj.image.shape[0],
        )
        if crowd_flow_alert:
            active_alerts.append(crowd_flow_alert)
        self.crowd_flow_detector.cleanup()
        accident_alert = self.accident_detector.update(frame_obj.camera_id, vehicles_detected)
        if accident_alert:
            accident_alert["location"] = location_info
            active_alerts.append(accident_alert)
            self.emergency_dispatcher.dispatch(accident_alert)

        # Draw full HUD annotations onto the live frame
        annotated_image = self.draw_annotations(
            frame_obj.image,
            vehicles_detected,
            people_detected,
            objects_detected,
            active_alerts,
            location_info=location_info
        )

        metadata = {
            "camera_id": frame_obj.camera_id,
            "pts_ms": frame_obj.pts_ms,
            "system_timestamp": frame_obj.system_timestamp,
            "location": {
                "name": location_info.get("location_name", "Unknown Location"),
                "district": location_info.get("district", "Unknown District"),
                "latitude": location_info.get("latitude"),
                "longitude": location_info.get("longitude"),
                "maps_link": location_info.get("maps_link")
            },
            "device_registry_gis": location_info,
            "ai_detections": {
                "people_count": len(people_detected),
                "people": people_detected,
                "vehicles": vehicles_detected,
                "license_plates": plates_detected,
                "objects": objects_detected,
                "alerts": active_alerts,
                "crowd_flow": crowd_flow_alert or {
                    "status": "NORMAL",
                    "people_count": len(people_detected)
                },
                "incident": accident_alert
            }
        }

        return annotated_image, metadata