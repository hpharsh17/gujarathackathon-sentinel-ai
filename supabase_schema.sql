-- Supabase SQL Schema for Sentinel Hackathon: One Engine, Eight Capabilities

-- ENABLE VECTORS FOR FACE RECOGNITION
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Camera GIS Registry
CREATE TABLE IF NOT EXISTS camera_locations (
    camera_id TEXT PRIMARY KEY,
    location_name TEXT NOT NULL,
    district TEXT,
    latitude FLOAT,
    longitude FLOAT,
    maps_link TEXT
);

-- ==========================================
-- AI DETECTIONS LOGGING TABLES
-- ==========================================
-- These tables store the real-time AI results for the 8 capabilities.

-- Central Event Log (Every AI detection links back to a specific timestamp/frame)
CREATE TABLE IF NOT EXISTS ai_events (
    event_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    camera_id TEXT REFERENCES camera_locations(camera_id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    frame_image_url TEXT -- Link to Supabase Storage if you save the frame
);

-- Capability 1: People (Detection, Counting, Crowd Density)
CREATE TABLE IF NOT EXISTS log_people (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_id UUID REFERENCES ai_events(event_id) ON DELETE CASCADE,
    person_count INT,
    crowd_density_score FLOAT, -- e.g., 0.0 to 1.0
    bounding_boxes JSONB -- Store array of boxes
);

-- Capability 2 & 4: Vehicles & Attributes
CREATE TABLE IF NOT EXISTS log_vehicles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_id UUID REFERENCES ai_events(event_id) ON DELETE CASCADE,
    vehicle_type TEXT, -- Car, motorcycle, bus, truck
    color TEXT,
    make_model TEXT,
    confidence FLOAT,
    bounding_box JSONB
);

-- Capability 3: License Plates (ANPR)
CREATE TABLE IF NOT EXISTS log_license_plates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_id UUID REFERENCES ai_events(event_id) ON DELETE CASCADE,
    vehicle_id UUID REFERENCES log_vehicles(id) ON DELETE CASCADE,
    plate_text TEXT NOT NULL,
    confidence FLOAT
);

-- Cross-camera vehicle trail used for location-aware plate search.
CREATE TABLE IF NOT EXISTS cross_camera_vehicle_sightings (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    plate_text TEXT NOT NULL,
    camera_id TEXT REFERENCES camera_locations(camera_id),
    location_name TEXT,
    district TEXT,
    latitude FLOAT,
    longitude FLOAT,
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE (plate_text, camera_id, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_cross_camera_plate_time
ON cross_camera_vehicle_sightings (plate_text, observed_at DESC);

-- Capability 5: Objects (Abandoned / Suspicious)
CREATE TABLE IF NOT EXISTS log_objects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_id UUID REFERENCES ai_events(event_id) ON DELETE CASCADE,
    object_type TEXT, -- e.g., 'Backpack', 'Suitcase'
    stationary_time_seconds INT,
    is_suspicious BOOLEAN DEFAULT FALSE,
    bounding_box JSONB
);

-- Capability 6: Activities (Suspicious / Unusual Behavior)
CREATE TABLE IF NOT EXISTS log_activities (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_id UUID REFERENCES ai_events(event_id) ON DELETE CASCADE,
    activity_type TEXT, -- e.g., 'Running', 'Loitering', 'Fighting'
    severity_level TEXT, -- 'LOW', 'MEDIUM', 'HIGH'
    description TEXT
);

-- Capability 7 & 8: Watchlist & Face Recognition Database
-- (These are the predefined targets the AI is searching for)

CREATE TABLE IF NOT EXISTS watchlist_vehicles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    plate_text TEXT NOT NULL UNIQUE,
    make TEXT,
    color TEXT,
    status TEXT DEFAULT 'STOLEN',
    reported_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watchlist_faces (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    face_embedding vector(512), -- For Similarity Search
    reason TEXT,
    status TEXT DEFAULT 'WANTED'
);

-- ==========================================
-- DUMMY DATA INSERTS
-- ==========================================

INSERT INTO camera_locations (camera_id, location_name, district, latitude, longitude, maps_link) VALUES 
('cam01', 'Chiman bhai Bridge', 'Ahmedabad', 23.069309, 72.587112, 'https://www.google.com/maps?q=23.069309,72.587112'),
('cam02', 'RTO Circle', 'Ahmedabad', 23.07069, 72.57043, 'https://www.google.com/maps?q=23.57069,72.37043'),
('cam03', 'Subhash Bridge', 'Ahmedabad', 23.063429, 72.581242, 'https://www.google.com/maps?q=23.603429,72.381242'),
('cam04', 'Paldi Circle', 'Ahmedabad', 23.00959, 72.56188, 'https://www.google.com/maps?q=23.00959,72.56188')
ON CONFLICT (camera_id) DO NOTHING;

INSERT INTO watchlist_vehicles (plate_text, make, color, status) VALUES 
('GJ01AB1234', 'Hyundai Creta', 'White', 'STOLEN'),
('GJ01XX9999', 'Maruti Swift', 'Silver', 'WANTED_IN_ROBBERY')
ON CONFLICT (plate_text) DO NOTHING;
