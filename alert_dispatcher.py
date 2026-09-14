"""Guarded emergency incident dispatch with dry-run as the default."""

import json
import os
import threading
import time
import urllib.request


class EmergencyDispatcher:
    def __init__(self, incident_file: str = "latest_incident.json"):
        self.incident_file = incident_file
        self.lock = threading.Lock()
        self.last_dispatch_at = 0.0

    def dispatch(self, incident: dict) -> dict:
        """Persist every incident; POST to an explicitly configured webhook only."""
        incident = {**incident, "dispatch_status": "RECORDED", "dispatch_time": time.time()}
        with self.lock:
            try:
                with open(self.incident_file, "w") as incident_file:
                    json.dump(incident, incident_file, indent=2)
            except OSError as error:
                incident["dispatch_status"] = f"RECORD_FAILED: {error}"

            webhook = os.getenv("EMERGENCY_WEBHOOK_URL", "").strip()
            production_mode = os.getenv("EMERGENCY_DISPATCH_MODE", "dry_run").lower() == "production"
            if webhook and production_mode:
                payload = json.dumps(incident).encode("utf-8")
                request = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(request, timeout=5) as response:
                        incident["dispatch_status"] = f"WEBHOOK_SENT:{response.status}"
                except Exception as error:
                    incident["dispatch_status"] = f"WEBHOOK_FAILED: {error}"
            else:
                incident["dispatch_status"] = "DRY_RUN_RECORDED"
        return incident 