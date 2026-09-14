# Sentinel Vision AI — Internal Master Technical Plan

> This is the internal engineering blueprint. It covers the full concept, all AI model decisions, cascade logic, data flow, and phase-by-phase roadmap for the development team.

---

## 1. System Concept & Vision

The Sentinel Vision AI platform is a **hybrid AI surveillance engine** combining two Hackathon models:

- **Model 2 (Unified Viewing):** One centralized AI engine processes all RTSP camera feeds and produces unified metadata, video relay, and analytics from a single interface.
- **Model 3 (VMS Federation):** A middleware API Gateway sits between the central engine and downstream departments. Each department only receives the data they are authorized to see based on their role.

The central idea is **"One Engine, Eight Capabilities"** — a single AI pipeline that can simultaneously detect people, vehicles, license plates, vehicle attributes, abandoned objects, suspicious activities, faces, and match against live watchlists. Each capability is a separate specialist AI model that is only invoked when the base detector finds a relevant object, making it highly efficient on GPU resources.

---

## 2. The 8 AI Capabilities — Model Decisions & Concepts

### Capability 1: People Detection & Counting
- **What it does:** Detects all persons in the frame, counts them, and estimates crowd density.
- **Model Decision:** YOLOv8x (Extra Large) with the ByteTrack tracker for consistent person ID across frames.
- **Why:** YOLOv8x gives the best balance of accuracy and speed on a GPU. ByteTrack prevents counting the same person twice when they move.
- **Trigger:** Always runs on every frame as part of the Layer 1 base scan.
- **Output stored in:** `log_people` table (Supabase).

### Capability 2: Vehicle Detection
- **What it does:** Detects vehicles — cars, motorcycles, buses, trucks, auto-rickshaws — and draws bounding boxes.
- **Model Decision:** Same YOLOv8x base model as Capability 1. COCO dataset classes 2 (car), 3 (motorcycle), 5 (bus), 7 (truck) are used.
- **Why:** Reusing the same single base YOLO pass for both People and Vehicles avoids running the model twice and wastes no GPU time.
- **Trigger:** Always runs as part of the Layer 1 base scan.
- **Output stored in:** `log_vehicles` table (Supabase).

### Capability 3: License Plate Recognition (ANPR)
- **What it does:** Crops each detected vehicle bounding box from Capability 2, runs a specialized plate detection model to find the license plate region, then applies OCR to extract the plate text.
- **Model Decision:** YOLOv8n-Plate (a fine-tuned lightweight model for plate detection) + EasyOCR for text extraction. PaddleOCR is a backup option for better Indic script performance.
- **Why:** Running ANPR on the full 1080p frame is inefficient and inaccurate. Cropping to just the vehicle region drastically reduces noise and improves OCR quality.
- **Trigger:** Only fires when a vehicle bounding box from Capability 2 is detected AND its pixel area exceeds a minimum threshold (too small = plate is unreadable anyway, skip it to save GPU).
- **Output stored in:** `log_license_plates` table (Supabase), linked to the `log_vehicles` row.

### Capability 4: Vehicle Attributes (Colour, Type, Make/Model)
- **What it does:** Classifies the colour, body type (sedan, SUV, hatchback, truck), and make/model of each detected vehicle.
- **Model Decision:** ResNet-50 classifier fine-tuned on Indian vehicle datasets. Runs on the same vehicle crop as Capability 3.
- **Why:** Both Capability 3 and Capability 4 share the exact same vehicle crop input. By batching them together in one network call, we avoid re-cropping the image twice.
- **Trigger:** Same trigger as Capability 3.
- **Output stored in:** `log_vehicles` table (colour and make columns).

### Capability 5: Abandoned / Suspicious Object Detection
- **What it does:** Detects objects like backpacks, suitcases, and handbags. If one remains stationary in the same position for more than 60 seconds without a person standing nearby, it is flagged as a suspicious abandoned object.
- **Model Decision:** YOLOv8x (same base model, COCO classes 24/26/28 for bags/suitcases). A lightweight centroid tracker in memory maintains the object's history.
- **Why:** The 60-second stationary timer eliminates false positives from people briefly putting their bags down.
- **Trigger:** Fires when an object class is found in the Layer 1 base scan. The timer logic runs in a lightweight Python dictionary in RAM (no GPU needed for the timer itself).
- **Output stored in:** `log_objects` table (Supabase).

### Capability 6: Suspicious / Unusual Activity Detection
- **What it does:** Analyses the body pose and movement patterns of detected persons to identify running, loitering, fighting, or trespassing.
- **Model Decision:** YOLOv8-Pose model, which outputs 17 skeleton keypoints per person. A heuristic vector analysis engine then evaluates the keypoint velocities and angles to classify activity type.
- **Why:** Pose-based analysis is more reliable than pixel-based optical flow for activity classification because it focuses on the human skeleton and is not confused by background movement (trees, flags, traffic).
- **Trigger:** Only fires per-person crop when a person bounding box from Capability 1 is detected.
- **Output stored in:** `log_activities` table (Supabase).

### Capability 7: Face Recognition (Missing / Wanted Persons)
- **What it does:** Generates a unique 512-dimensional embedding vector for each visible face. This vector mathematically represents the face and is used to search the Watchlist database for matches.
- **Model Decision:** InsightFace framework using the ArcFace backbone (`w600k_mbf.onnx`). This is the same technology used in law enforcement biometric systems globally.
- **Why:** ArcFace vectors allow for tolerance to lighting variation, partial occlusion (sunglasses, masks at an angle), and aging. It does not store face images — only mathematical vectors, which is more privacy-respecting.
- **Trigger:** Only fires when a person crop from Capability 1 has a detectable face region that is larger than 50×50 pixels (too small = face is not recognizable, skip it).
- **Output:** Face embedding vector (512 floats) sent directly to the Supabase Watchlist engine (Capability 8).

### Capability 8: Real-Time Watchlist Engine
- **What it does:** Matches incoming license plate text and face embedding vectors against the central law enforcement watchlist database in real time.
- **How it works for Plates:** Exact-match query against the `watchlist_vehicles` table. If `GJ01AB1234` is in the stolen vehicles registry, an alert fires instantly.
- **How it works for Faces:** Uses Supabase `pgvector` extension to perform a cosine similarity search. It finds the closest match in the `watchlist_faces` table. If the distance is below a confidence threshold, an alert fires.
- **Why pgvector:** Traditional SQL databases cannot search through thousands of 512-dimensional float vectors efficiently. `pgvector` adds a specialized index (IVFFlat) that can search millions of face embeddings in under 5 milliseconds.
- **Output stored in:** Alert payload attached to the relevant event in `ai_events` and flagged across all downstream dashboards.

---

## 3. The 3-Layer Cascade Execution Concept

This is the core multi-request management strategy. Instead of running all 8 models on every frame (which would be 8× slower), models are triggered conditionally:

**Layer 1 — The Base Scan (Runs on 100% of frames)**
One single GPU pass with YOLOv8x scans the full frame and produces three buckets: People crops, Vehicle crops, Object crops. This is the only model guaranteed to run every frame.

**Layer 2 — The Conditional Classifiers (Runs only when Layer 1 finds something)**
Each bucket from Layer 1 independently triggers its relevant specialist models. A frame with no vehicles in it completely skips the ANPR and Vehicle Attribute models. A dark night-time frame with no visible faces completely skips Face Recognition. This conditional triggering is what makes the system feasible on a single GPU node.

**Layer 3 — The Watchlist & Logging (Runs when Layer 2 produces results)**
Extracted plate text or face embeddings are sent as lightweight API queries to Supabase Cloud. This step runs asynchronously so it never slows down the video frame rate.

---

## 4. Frame Queue & Batch Processing Concept

The current code processes one camera sequentially. To scale to 50 cameras, the architecture uses a Redis in-memory queue:

- **Frame Grabbers (50 processes, lightweight):** One tiny process per camera grabs frames and pushes them into a shared Redis queue. These use almost no CPU — just network I/O.
- **The Queue (Redis):** Acts like a kitchen counter. All frames from all cameras pile up in a single FIFO line regardless of which camera they came from.
- **GPU Batch Workers (3–5 processes, heavy):** Each worker pulls 64 frames at once from the queue, stacks them into a single GPU tensor, and runs the Layer 1 base YOLO scan in one GPU call. This is 30–50× faster than running YOLO 64 times individually.
- **Auto-Scaling:** At 3 AM when cameras are quiet, the queue is nearly empty. At peak traffic hours the queue grows and additional GPU worker processes can be spawned to drain it faster.

---

## 5. Database Design Concept (9 Tables)

The Supabase schema is designed around a central `ai_events` table as the backbone. Every single detection — whether a vehicle, a person, or a suspicious object — is linked back to one event row that records the camera ID, timestamp, and optionally the stored frame image URL. The 8 capability-specific tables (`log_people`, `log_vehicles`, `log_license_plates`, etc.) are child tables that reference `ai_events` via a foreign key. This relational design allows extremely powerful cross-capability queries like:

> *"Show me every White SUV detected at Paldi Circle between 2PM and 4PM that also had a detected person nearby and was flagged by the watchlist."*

---

## 6. Docker Containerization & Production Packaging Strategy

While `requirements.txt` is useful for fast local development, handing a raw Python virtual environment to judges or enterprise clients frequently breaks due to:
- **CUDA/Driver Mismatches:** Host NVIDIA driver vs PyTorch CUDA runtime conflicts.
- **Missing OS-Level Binaries:** OpenCV GUI libraries (`libgl1-mesa-glx`, `libglib2.0-0`), FFmpeg codecs, and C++ compiler tools (`build-essential`).
- **Path and OS Differences:** Windows backslashes vs Linux forward slashes, environment variables.

### The Docker Architecture Plan:
1. **Container Base:**
   - Base Image: `pytorch/pytorch:2.1.2-cuda11.8-cudnn8-runtime` (Ubuntu 22.04 + CUDA 11.8 + cuDNN 8 pre-configured).
   - Pre-installed system dependencies: FFmpeg, OpenCV headless runtime, Git, build tools.
2. **GPU Passthrough:**
   - Uses NVIDIA Container Toolkit (`--gpus all` / `deploy.resources.reservations.devices`).
   - Grants full hardware acceleration directly to PyTorch and TensorRT without host-side Python dependencies.
3. **Multi-Service Composition (`docker-compose.yml`):**
   - **Service 1: `redis`** (In-memory frame bus for 50+ cameras).
   - **Service 2: `stream-ingest`** (Multi-RTSP stream grabbers feeding frames into Redis).
   - **Service 3: `ai-engine`** (GPU worker running 8-Capability Cascade Engine with CUDA).
   - **Service 4: `api-gateway`** (FastAPI federated middleware and WebSockets).
4. **Estimated Footprint & Distribution:**
   - Uncompressed Image: ~6.5 GB
   - Compressed Image: ~2.8 GB
   - Judges execute a single command: `docker compose up --build` or import `sentinel_ai_v1.tar.gz`.

---

## 7. Next-Gen Cyber Command GUI Specification (Phase 4)

Standard OpenCV (`cv2.imshow`) is an image-debugging tool designed to render raw pixel matrices onto basic Win32 window handles. It cannot natively support interactive tabs, multi-camera matrix grids, search filtering, Leaflet GIS vector maps, animated DOM elements, or responsive CSS layouts.

To deliver an enterprise-grade visual experience aligned with the official Hackathon guidelines, the Phase 4 GUI is built as a **Cyberpunk Tactical Operations Center** powered by a **React.js SPA (Vite + React + Tailwind CSS + React-Leaflet + Lucide Icons)** connected via **WebSockets to a Python FastAPI microservice**.

### 🛠️ Frontend & Middleware Technology Alignment
- **Frontend Framework:** **React.js** (Component-driven state management for multi-camera feeds and target scanner panels).
- **Styling & HUD Effects:** **Tailwind CSS + Custom Cyberpunk Canvas / CSS Keyframes**.
- **GIS Engine:** **React-Leaflet / Leaflet.js** (CartoDB Dark Matter tactical map layer).
- **Real-Time Data Streaming:** **WebSockets (FastAPI)** delivering 60 FPS telemetry, metadata, and cropped vehicle snapshots.
- **Role-Based Access Control:** **JWT-authenticated department portals** (Police vs Traffic vs Municipal).

### 🎨 Visual Theme & Cyberpunk Styling
- **Color Palette:**
  - Background: Deep Obsidian (`#0A0E17`) and Dark Slate (`#111827`)
  - Primary Accent: Holographic Neon Cyan (`#00F3FF`)
  - Secondary Accent: Tactical Electric Blue (`#0066FF`)
  - Alert Warnings: Pulsating Crimson (`#FF003C`)
  - Cleared/Status: Bio-Matrix Green (`#00FF88`)
  - Radar Telemetry: Neon Amber (`#FFB800`)
- **Cybernetic Elements (Inspired by Design References):**
  - Holographic rotating orbital telemetry rings & concentric radar sweeps.
  - Topographic wireframe grids and frequency audio wave graphs.
  - Glowing laser-sweep scanning animations over extracted vehicle and person crops.
  - Sci-fi target reticles with tracking lock-on indicators.
- **Reference Assets:** Saved in `e:\Hackathon\docs\ui_references\` (`media_1789065137275.png`, `media_1789065143336.png`, `media_1789065150299.png`).

---

### 🖥️ Tab Architecture & Capabilities

#### 1. Tab 1: Multi-Camera Surveillance Matrix (9-Camera Grid)
- **3×3 Matrix Layout:** Simultaneously renders 9 live camera feeds (e.g. `cam01` through `cam09` or customized selections).
- **Interactive Camera Cards:**
  - Header: Camera ID (`CAM08`), Location Name, District, and live FPS indicator.
  - Click-to-Zoom: Clicking any of the 9 tiles instantly zooms in to full-screen focused surveillance mode.
- **Dynamic Camera Search & Filter Bar:**
  - Search by `camera_id` (e.g. `cam08`), district (`Junagadh`, `Ahmedabad`), or road name (`Majewadi Gate`).
  - Instantly filters the grid down to matching cameras.

#### 2. Tab 2: Gujarat Tactical GIS Command Map
- **Interactive Vector Map:** Powered by Leaflet.js with CartoDB Dark Matter tiles, auto-centered on the Gujarat region (`22.2587° N, 71.1924° E`).
- **Geocoded Camera Nodes:**
  - All 30 cameras mapped accurately using latitude and longitude from the Supabase registry.
  - Glowing circular radar-ping animations around active camera coordinates.
  - Color-coded status markers:
    - 🟢 Green: Normal traffic flow, zero alerts.
    - 🟡 Amber: High crowd density or vehicle congestion.
    - 🔴 Red: Active Watchlist hit (stolen vehicle or wanted person detected).
- **Live Node Popups:** Clicking any map pin reveals camera metadata, coordinates, live detection count, and a direct button to view its live feed.

#### 3. Tab 3: Single-Camera Focus & AI Target Scanner
- **Primary Video Viewport:** Large full-resolution feed of the selected camera with real-time YOLO bounding boxes.
- **Right-Side Target Extraction Panel:**
  - When a vehicle or person is detected, the pipeline automatically crops out the target and slides it into the right-side scanner queue.
  - **Visual Scanning Animation:** A glowing neon-cyan laser sweep line travels vertically across the crop with a radar sound/glow effect.
  - **Live Database Query Feedback:**
    - State 1: `SCANNING WATCHLIST DATABASE...` (flashing amber)
    - State 2: `CLEARED - NO FLAGS` (solid green badge)
    - State 3: `CRITICAL ALERT: MATCH FOUND IN STOLEN VEHICLES REGISTRY` (pulsating crimson siren border with plate number and timestamp).

#### 4. Tab 4: Central Command ("God Mode" Unified Center)
- **Combined Command Dashboard:**
  - Central active camera viewport flanked by telemetry widgets.
  - Rotating concentric cyber-rings and biometric holographic indicators in the top corner.
  - Live system telemetry: GPU VRAM utilization, queue throughput, AI inference latency, active camera count.
  - Embedded Gujarat tactical mini-map with real-time incident pings.
  - Live scrolling security log terminal streaming real-time JSON detection events.

---

## 8. Phase-by-Phase Roadmap

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Supabase 9-Table Schema, GIS Camera Registry Migration from Excel, Stolen Vehicle Watchlist Query | ✅ COMPLETED |
| **Phase 1** | Dynamic CUDA GPU Auto-Detection in all AI models with silent CPU fallback, DEPLOYMENT.md for judges | ✅ COMPLETED |
| **Phase 2** | In-Memory Frame Queue Manager (`frame_queue.py`), Multi-Camera StreamGrabber, Batch processing | ✅ COMPLETED |
| **Phase 3** | Full 8-Capability Cascade Engine in `pipeline.py` (Vehicles, People, ANPR, Attributes, Bags, Activity, Face, Watchlist) | ✅ COMPLETED |
| **Phase 4** | Next-Gen Cyber Command GUI (React.js + Tailwind CSS, FastAPI Backend `server.py`, 4 Tactical Tabs, Leaflet Gujarat Map, Laser Scanner Panel) | ✅ COMPLETED |
| **Phase 5** | Production Docker Containerization (`Dockerfile`, `docker-compose.yml`, `requirements-docker.txt`, `run_c2_system.bat`) | ✅ COMPLETED |


