import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

class CameraDatabase:
    """
    Manages the Supabase Cloud Database connection for camera locations and watchlists.
    """
    def __init__(self):
        load_dotenv()
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        
        # Strip quotes if they were accidentally left in the .env string
        if url: url = url.strip('"').strip("'")
        if key: key = key.strip('"').strip("'")
            
        if not url or not key:
            print("Warning: Missing SUPABASE_URL or SUPABASE_KEY in .env file.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(url, key)
            
        self._camera_cache = {}

    def get_camera_info(self, camera_id: str) -> dict:
        """Fetch GIS metadata for a specific camera_id from Supabase (cached in memory)."""
        cid = camera_id.lower()
        if cid in self._camera_cache:
            return self._camera_cache[cid]

        if not self.supabase:
            return {}
            
        try:
            if self.supabase:
                response = self.supabase.table('camera_locations').select("*").eq('camera_id', cid).execute()
                if response.data and len(response.data) > 0:
                    data = response.data[0]
                    self._camera_cache[cid] = data
                    return data
        except Exception as e:
            print(f"Supabase DB Warning (get_camera_info): {e}")

        # Enterprise Offline / RLS Fallback Registry (All 30 Cameras)
        fallback = self.LOCAL_REGISTRY.get(cid)
        if fallback:
            self._camera_cache[cid] = fallback
            return fallback
            
        return {}

    # Static Registry populated from Camera_location.xlsx
    LOCAL_REGISTRY = {
        "cam01": {"camera_id": "cam01", "location_name": "Chiman Bhai Bridge", "district": "Ahmedabad", "latitude": 23.069309, "longitude": 72.587112, "maps_link": "https://www.google.com/maps?q=23.069309,72.587112"},
        "cam02": {"camera_id": "cam02", "location_name": "Janpath", "district": "Mehsana", "latitude": 23.57069, "longitude": 72.37043, "maps_link": "https://www.google.com/maps?q=23.57069,72.37043"},
        "cam03": {"camera_id": "cam03", "location_name": "O.N.G.C. Office", "district": "Mehsana", "latitude": 23.603429, "longitude": 72.381242, "maps_link": "https://www.google.com/maps?q=23.603429,72.381242"},
        "cam04": {"camera_id": "cam04", "location_name": "Paldi Circle", "district": "Ahmedabad", "latitude": 23.00959, "longitude": 72.56188, "maps_link": "https://www.google.com/maps?q=23.00959,72.56188"},
        "cam05": {"camera_id": "cam05", "location_name": "Visat Teen Rasta", "district": "Ahmedabad", "latitude": 23.095, "longitude": 72.583, "maps_link": "https://www.google.com/maps?q=23.095,72.583"},
        "cam06": {"camera_id": "cam06", "location_name": "Timbavadi Gate-Junagadh", "district": "Junagadh", "latitude": 21.50274, "longitude": 70.43514, "maps_link": "https://www.google.com/maps?q=21.50274,70.43514"},
        "cam07": {"camera_id": "cam07", "location_name": "Hero Showroom-Gir Somnath", "district": "Gir Somnath", "latitude": 20.793, "longitude": 70.703, "maps_link": "https://www.google.com/maps?q=20.793,70.703"},
        "cam08": {"camera_id": "cam08", "location_name": "Majewadi Gate-Junagadh", "district": "Junagadh", "latitude": 21.535461, "longitude": 70.460092, "maps_link": "https://www.google.com/maps?q=21.535461,70.460092"},
        "cam09": {"camera_id": "cam09", "location_name": "New Bypass Near By Circle-Junagadh-2", "district": "Junagadh", "latitude": 21.55, "longitude": 70.45, "maps_link": "https://www.google.com/maps?q=21.55,70.45"},
        "cam10": {"camera_id": "cam10", "location_name": "Char Chowk Road-2-Junagadh", "district": "Junagadh", "latitude": 21.52, "longitude": 70.46, "maps_link": "https://www.google.com/maps?q=21.52,70.46"},
        "cam11": {"camera_id": "cam11", "location_name": "Dolatpara-Junagadh", "district": "Junagadh", "latitude": 21.553206, "longitude": 70.47083, "maps_link": "https://www.google.com/maps?q=21.553206,70.470830"},
        "cam12": {"camera_id": "cam12", "location_name": "In Mandir Adalaj Tolnaka", "district": "Gandhinagar", "latitude": 23.17, "longitude": 72.58, "maps_link": "https://www.google.com/maps?q=23.17,72.58"},
        "cam13": {"camera_id": "cam13", "location_name": "CN Vidhyalaya", "district": "Ahmedabad", "latitude": 23.021642, "longitude": 72.551358, "maps_link": "https://www.google.com/maps?q=23.021642,72.551358"},
        "cam14": {"camera_id": "cam14", "location_name": "Delight RLVD", "district": "Ahmedabad", "latitude": None, "longitude": None, "maps_link": None},
        "cam15": {"camera_id": "cam15", "location_name": "Suvidha Park", "district": "Ahmedabad", "latitude": 23.06, "longitude": 72.65, "maps_link": "https://www.google.com/maps?q=23.06,72.65"},
        "cam16": {"camera_id": "cam16", "location_name": "Visat P2", "district": "Ahmedabad", "latitude": 23.095, "longitude": 72.583, "maps_link": "https://www.google.com/maps?q=23.095,72.583"},
        "cam17": {"camera_id": "cam17", "location_name": "Rajkot Bus Port CCTV", "district": "Rajkot", "latitude": 22.291, "longitude": 70.8023, "maps_link": "https://www.google.com/maps?q=22.291,70.8023"},
        "cam18": {"camera_id": "cam18", "location_name": "Rajkot CCTV", "district": "Rajkot", "latitude": 22.3, "longitude": 70.8, "maps_link": "https://www.google.com/maps?q=22.30,70.80"},
        "cam19": {"camera_id": "cam19", "location_name": "KHAPARIA GRAM PANCHAYAT, TALUKA GANDEVI, DISTRICT NAVSARI", "district": "Navsari", "latitude": 20.9131, "longitude": 72.85065, "maps_link": "https://www.google.com/maps?q=20.9131,72.85065"},
        "cam20": {"camera_id": "cam20", "location_name": "Mohanpura", "district": "Navsari", "latitude": 20.85358, "longitude": 72.94662, "maps_link": "https://www.google.com/maps?q=20.85358,72.94662"},
        "cam21": {"camera_id": "cam21", "location_name": "Patan Dethali Char Rasta", "district": "Patan", "latitude": 23.931208, "longitude": 72.362684, "maps_link": "https://www.google.com/maps?q=23.931208,72.362684"},
        "cam22": {"camera_id": "cam22", "location_name": "BK Mervada Tran Rasta", "district": "Patan", "latitude": 23.75, "longitude": 72.2, "maps_link": "https://www.google.com/maps?q=23.75,72.20"},
        "cam23": {"camera_id": "cam23", "location_name": "Kheram", "district": "Navsari", "latitude": 20.6313, "longitude": 73.0951, "maps_link": "https://www.google.com/maps?q=20.6313,73.0951"},
        "cam24": {"camera_id": "cam24", "location_name": "Dehgam", "district": "Navsari", "latitude": 20.80163, "longitude": 73.08505, "maps_link": "https://www.google.com/maps?q=20.80163,73.08505"},
        "cam25": {"camera_id": "cam25", "location_name": "Dhanori", "district": "Navsari", "latitude": 20.8387, "longitude": 73.0238, "maps_link": "https://www.google.com/maps?q=20.8387,73.0238"},
        "cam26": {"camera_id": "cam26", "location_name": "TANKAL", "district": "Navsari", "latitude": 20.85704, "longitude": 73.13053, "maps_link": "https://www.google.com/maps?q=20.85704,73.13053"},
        "cam27": {"camera_id": "cam27", "location_name": "Bilimora", "district": "Navsari", "latitude": 20.7696, "longitude": 72.9613, "maps_link": "https://www.google.com/maps?q=20.7696,72.9613"},
        "cam28": {"camera_id": "cam28", "location_name": "Bilimora", "district": "Navsari", "latitude": 20.7696, "longitude": 72.9613, "maps_link": "https://www.google.com/maps?q=20.7696,72.9613"},
        "cam29": {"camera_id": "cam29", "location_name": "Bilimora", "district": "Navsari", "latitude": 20.7696, "longitude": 72.9613, "maps_link": "https://www.google.com/maps?q=20.7696,72.9613"},
        "cam30": {"camera_id": "cam30", "location_name": "Gandhidham Rambaugh P2", "district": "Kutch", "latitude": 23.0744, "longitude": 70.0977, "maps_link": "https://www.google.com/maps?q=23.0744,70.0977"}
    }

    def check_stolen_vehicle(self, plate_text: str) -> dict:
        """Query the Supabase Watchlist to see if a license plate is stolen/wanted."""
        if not self.supabase:
            return {}
            
        # Clean the text (remove spaces/dashes) for robust matching
        clean_plate = plate_text.replace(" ", "").replace("-", "").upper()
        
        try:
            response = self.supabase.table('stolen_vehicles').select("*").eq('plate_text', clean_plate).execute()
            if response.data and len(response.data) > 0:
                return response.data[0] # Returns the record if it's a match!
            return {}
        except Exception as e:
            print(f"Supabase DB Error (check_stolen_vehicle): {e}")
            return {}

    def record_vehicle_sighting(self, plate_text: str, camera_info: dict, observed_at: float) -> bool:
        """Persist one normalized ANPR sighting for cross-camera search."""
        if not self.supabase:
            return False
        record = {
            "plate_text": plate_text.replace(" ", "").replace("-", "").upper(),
            "camera_id": camera_info.get("camera_id"),
            "location_name": camera_info.get("location_name"),
            "district": camera_info.get("district"),
            "latitude": camera_info.get("latitude"),
            "longitude": camera_info.get("longitude"),
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(observed_at)),
        }
        try:
            self.supabase.table("cross_camera_vehicle_sightings").insert(record).execute()
            return True
        except Exception as error:
            print(f"Supabase DB Warning (record_vehicle_sighting): {error}")
            return False

    def get_vehicle_sightings(self, plate_text: str) -> list:
        """Read recent sightings for a normalized plate from Supabase."""
        if not self.supabase:
            return []
        clean_plate = plate_text.replace(" ", "").replace("-", "").upper()
        try:
            response = (self.supabase.table("cross_camera_vehicle_sightings")
                        .select("camera_id,location_name,district,latitude,longitude,observed_at")
                        .eq("plate_text", clean_plate)
                        .order("observed_at", desc=True)
                        .limit(50)
                        .execute())
            sightings = []
            for sighting in response.data or []:
                value = sighting.get("observed_at")
                if isinstance(value, str):
                    value = value.replace("Z", "+00:00")
                    import datetime
                    observed_at = datetime.datetime.fromisoformat(value).timestamp()
                else:
                    observed_at = value
                sightings.append({**sighting, "observed_at": observed_at})
            return sightings
        except Exception as error:
            print(f"Supabase DB Warning (get_vehicle_sightings): {error}")
            return []

# Test script
if __name__ == "__main__":
    db = CameraDatabase()
    print("\n--- Testing Supabase Connection ---")
    print("Testing 'cam01':", db.get_camera_info('cam01'))
    print("Testing 'GJ01AB1234' on Watchlist:", db.check_stolen_vehicle('GJ01AB1234'))
