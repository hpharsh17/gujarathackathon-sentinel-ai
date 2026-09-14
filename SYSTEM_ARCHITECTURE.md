# Sentinel Vision AI — System Architecture
### Gujarat Hackathon Submission | Hybrid Model 2 + Model 3

---

## Overview

Sentinel Vision AI is a hybrid AI-powered CCTV surveillance platform that unifies video feeds from multiple departmental systems into a single intelligent engine, while simultaneously enforcing federated, role-based access for downstream government departments.

It implements **Model 2 (Unified Viewing & Metadata Analytics)** and **Model 3 (VMS Federation & Middleware Integration)** as a combined hybrid approach, enhanced with **cross-camera vehicle corridor tracking**, **accident & hazard detection**, **fluid-dynamic crowd flow analytics**, and **automated multi-agency emergency dispatch (Police, Fire, Ambulance)**.

---

## Master System Architecture

```mermaid
flowchart TD
    classDef cam fill:#1E293B,stroke:#0284C7,stroke-width:2px,color:#F8FAFC;
    classDef queue fill:#1E293B,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC;
    classDef base fill:#0F172A,stroke:#06B6D4,stroke-width:2px,color:#F8FAFC;
    classDef ai fill:#1E293B,stroke:#10B981,stroke-width:2px,color:#F8FAFC;
    classDef db fill:#1E293B,stroke:#8B5CF6,stroke-width:2px,color:#F8FAFC;
    classDef dispatch fill:#1E293B,stroke:#EF4444,stroke-width:2px,color:#F8FAFC;
    classDef gw fill:#1E293B,stroke:#EC4899,stroke-width:2px,color:#F8FAFC;
    classDef dept fill:#0F172A,stroke:#14B8A6,stroke-width:2px,color:#F8FAFC;

    %% ── LAYER 1: INGESTION ──
    subgraph L1["📷 LAYER 1: MULTI-CAMERA RTSP INGESTION NETWORK"]
        direction LR
        CAM_A["Node 01-10\nAhmedabad Corridors"]:::cam
        CAM_B["Node 11-20\nHighways & Toll Plazas"]:::cam
        CAM_C["Node 21-30+\nUrban & Border Junctions"]:::cam
    end

    %% ── LAYER 2: QUEUE ──
    subgraph L2["⚡ LAYER 2: HIGH-SPEED INGESTION BUFFER"]
        QUEUE["In-Memory Lossy-Drop FIFO Queue (`frame_queue.py`)\nAtomic Writes · Sub-25ms Latency · Scalable to Kafka/Redis"]:::queue
    end

    %% ── LAYER 3: AI PIPELINE ──
    subgraph L3["🧠 LAYER 3: 12-CAPABILITY AI CASCADING PIPELINE"]
        direction TB
        YOLO["Layer 3.1: Base Detection & Tracking (YOLOv8x + ByteTrack)\nScans 100% of frames on GPU in single FP16 tensor pass"]:::base
        
        subgraph MODULES["12 Dedicated AI Capabilities (Parallel Cascade)"]
            direction LR
            
            subgraph MOD_V["🚗 Vehicle & Corridor Intelligence"]
                direction TB
                V1["Cap 2: Vehicle Type Classification (Car, Bus, Truck, Rickshaw)"]:::ai
                V2["Cap 3: ANPR OCR (License Plate Extraction)"]:::ai
                V3["Cap 4: Vehicle Attributes (Color, Make & Model)"]:::ai
                V4["Cap 8: Real-Time Stolen Vehicle Watchlist Match"]:::ai
                V5["Cap 9: Cross-Camera Corridor Velocity & Interception"]:::ai
            end

            subgraph MOD_P["👥 Crowd & Human Dynamics"]
                direction TB
                P1["Cap 1: People Count & Density Heatmap Index"]:::ai
                P2["Cap 6: Behavior Tracking (Violence, Loitering, Running)"]:::ai
                P3["Cap 11: Crowd Flow Hydrodynamics (Surge & Vortex)"]:::ai
            end

            subgraph MOD_S["🚨 Identity, Safety & Autonomous Dispatch"]
                direction TB
                S1["Cap 5: Stationary Abandoned Objects (Timer >60s)"]:::ai
                S2["Cap 7: Face Recognition (ArcFace 512-d Vector)"]:::ai
                S3["Cap 10: Kinematic Crash Deceleration & Fire Bloom"]:::ai
                S4["Cap 12: Automated Agency Dispatch Router (112, 101, 108)"]:::ai
            end
        end
    end

    %% ── LAYER 4 & 5: STORAGE & DISPATCH ──
    subgraph L4_L5["DATA BACKBONE & INCIDENT DISPATCH"]
        direction LR
        
        subgraph L4["☁️ LAYER 4: DATABASE & GIS"]
            direction TB
            DATABASE[("PostgreSQL + PostGIS + pgvector\n9 Relational Tables · GIS Registry\nVector Search · Offline Fallback")]:::db
        end

        subgraph L5["📢 LAYER 5: EMERGENCY DISPATCHER"]
            direction TB
            DISPATCH["Automated Dispatcher (`alert_dispatcher.py`)\nIncident Triage & Webhook Router"]:::dispatch
            DISPATCH --> D_POLICE["🚔 Police Control Room"]:::dispatch
            DISPATCH --> D_FIRE["🚒 Fire & Rescue Department"]:::dispatch
            DISPATCH --> D_EMS["🚑 Ambulance & EMS"]:::dispatch
        end
    end

    %% ── LAYER 6: GATEWAY ──
    subgraph L6["🛡️ LAYER 6: FEDERATED RBAC MIDDLEWARE (MODEL 3)"]
        GATEWAY["FastAPI Federated Gateway (`server.py`)\nJWT Auth · Data Masking · WebSocket Streams · MJPEG Relay"]:::gw
    end

    %% ── LAYER 7: CLIENTS ──
    subgraph L7["💻 LAYER 7: DEPARTMENT TACTICAL COMMAND HUDS"]
        direction LR
        D_POL["🚔 POLICE C2\nFull Feeds · Stolen Watchlist\nSuspects · Intercept Paths"]:::dept
        D_TRF["🚦 TRAFFIC CONTROL\nANPR Hits · Corridor Speeds\nCongestion · Accidents"]:::dept
        D_MUN["🏛️ MUNICIPAL CORP\nCrowd Surges · Fire Alerts\nGIS Infrastructure"]:::dept
    end

    %% ── CONNECTIONS ──
    L1 -->|RTSP TCP Streams| QUEUE
    QUEUE -->|Dynamic Batching| YOLO
    YOLO -->|Vehicle Crops| MOD_V
    YOLO -->|Person Crops| MOD_P
    YOLO -->|Object & Thermal Crops| MOD_S

    MOD_V & MOD_P & MOD_S -->|Telemetry & Feature Vectors| DATABASE
    MOD_V & MOD_P & MOD_S -->|High-Priority Anomalies| DISPATCH

    DATABASE <-->|Secure API Query / Event Bus| GATEWAY
    GATEWAY -->|RBAC Filtered Feeds| D_POL
    GATEWAY -->|Redacted Traffic View| D_TRF
    GATEWAY -->|Redacted Municipal View| D_MUN
```

---

## One Engine, 12 Core Capabilities

```mermaid
flowchart TD
    classDef main fill:#0F172A,stroke:#06B6D4,stroke-width:2px,color:#F8FAFC;
    classDef vCore fill:#1E293B,stroke:#0284C7,stroke-width:2px,color:#F8FAFC;
    classDef pCore fill:#1E293B,stroke:#10B981,stroke-width:2px,color:#F8FAFC;
    classDef sCore fill:#1E293B,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC;

    Engine["🧠 SENTINEL C2 AI UNIFIED ENGINE"]:::main

    %% Vertical Group 1
    subgraph G1["🚗 DOMAIN 1: VEHICLE & CORRIDOR INTELLIGENCE"]
        direction TB
        C2["2. Vehicle Classification (Car, Truck, Bus, Rickshaw)"]:::vCore
        C3["3. ANPR License Plate OCR Extraction"]:::vCore
        C4["4. Vehicle Color, Make & Model Profiling"]:::vCore
        C8["8. Real-Time Stolen Vehicle Watchlist Match"]:::vCore
        C9["9. Cross-Camera Corridor Velocity & Interception"]:::vCore
    end

    %% Vertical Group 2
    subgraph G2["👥 DOMAIN 2: PEDESTRIAN & CROWD DYNAMICS"]
        direction TB
        C1["1. People Detection & Density Heatmap Index"]:::pCore
        C6["6. Suspicious Behavior (Violence, Loitering, Running)"]:::pCore
        C11["11. Fluid Crowd Dynamics (Stampede & Vortex Surge)"]:::pCore
    end

    %% Vertical Group 3
    subgraph G3["🚨 DOMAIN 3: SAFETY, HAZARDS & AGENCY DISPATCH"]
        direction TB
        C5["5. Stationary Abandoned Object Detection (>60s)"]:::sCore
        C7["7. ArcFace 512-d Facial Vector Recognition"]:::sCore
        C10["10. Kinematic Crash Deceleration & Fire Bloom Detection"]:::sCore
        C12["12. Automated Multi-Agency Dispatch (Police, Fire & EMS Control Rooms)"]:::sCore
    end

    Engine --> G1
    G1 --> G2
    G2 --> G3
```

---

## 4-Layer AI Cascade Execution Flow

The system executes in a **hierarchical cascade** to eliminate unnecessary computation. Higher-level neural networks only run if the primary pass detects target regions of interest:

```mermaid
flowchart TD
    classDef base fill:#0F172A,stroke:#06B6D4,stroke-width:2px,color:#F8FAFC;
    classDef trigger fill:#1E293B,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC;
    classDef model fill:#1E293B,stroke:#8B5CF6,stroke-width:2px,color:#F8FAFC;
    classDef db fill:#1E293B,stroke:#10B981,stroke-width:2px,color:#F8FAFC;
    classDef dispatch fill:#1E293B,stroke:#EF4444,stroke-width:2px,color:#F8FAFC;

    Frame["📹 Incoming Video Frame\n(1080p RTSP Stream over TCP)"]:::base --> L1["Layer 1 — Base YOLO Scan\nRuns on 100% of frames in single FP16 GPU pass (<12ms)"]:::base

    L1 --> R{"Primary Entity\nDetected?"}:::trigger

    %% Vehicle Path
    R -->|Vehicle ROI| VB["Crop Vehicle Region"]:::trigger
    VB --> ANPR["Cap 3: ANPR OCR (Plate Text)"]:::model
    VB --> Attr["Cap 4: Color, Type & Category"]:::model
    VB --> CrashCheck{"Kinematic Decel\n>40px/s or IoU>0.4?"}:::trigger
    CrashCheck -->|Yes| CrashAlert["Cap 10: Vehicle Collision Alert"]:::dispatch

    %% Person Path
    R -->|Person ROI| PB["Crop Person Region"]:::trigger
    PB --> FaceCheck{"Face Area\n> 50x50 px?"}:::trigger
    FaceCheck -->|Yes| FR["Cap 7: ArcFace 512-d Vector"]:::model
    PB --> Pose["Cap 6: Behavior Analysis (Fight/Run)"]:::model
    PB --> Flow["Cap 11: Crowd Flow Fluid Dynamics"]:::model

    %% Object Path
    R -->|Unattended Item| OB["Cap 5: Stationary Timer (>60s)"]:::model

    %% Corridor correlation
    ANPR --> CC["Cap 9: Cross-Camera Correlator\nDistance + Elapsed Time -> Speed km/h"]:::model
    
    ANPR & Attr & FR & Pose & CrashAlert & Flow & OB & CC --> Supa["Layer 4 — Supabase Cloud DB\npgvector Match + GIS Geocoded Storage"]:::db

    %% Automated Emergency Dispatch
    CrashAlert --> Dispatcher["Layer 4 — Emergency Dispatcher (`alert_dispatcher.py`)\nTriage by incident severity"]:::dispatch
    Flow -->|Stampede Warning| Dispatcher
    ANPR -->|Stolen Watchlist Hit| Dispatcher

    Dispatcher --> P_Out["🚔 Police Control Room"]:::dispatch
    Dispatcher --> F_Out["🚒 Fire & Rescue Department"]:::dispatch
    Dispatcher --> A_Out["🚑 Ambulance & EMS"]:::dispatch
```

---

## Automated Multi-Agency Emergency Dispatch Matrix

When an anomaly or watchlist hit is confirmed, the **Emergency Dispatcher** (`alert_dispatcher.py`) triages the event based on incident taxonomy and issues real-time webhooks with geocoded metadata:

| Incident Category | Detection Mechanism | Primary Agency | Secondary Agency | Automated Payload Dispatched |
|---|---|---|---|---|
| **Stolen Vehicle Identified** | ANPR OCR + `watchlist_vehicles` lookup | 🚔 **Police Control Room** | 🚦 Traffic Dept | Camera ID, Geolocation, Plate Number, Vehicle Color, Corridor Heading, Timestamp |
| **High-Speed Vehicle Collision** | Kinematic abrupt deceleration + bbox IoU overlap | 🚑 **Ambulance & EMS** | 🚔 Police Control Room | Collision GPS, Estimated Speed at Impact, Camera Snapshot URL, Lanes Blocked |
| **Fire / Smoke Hazard** | Chromatic flame bloom + stationary thermal rise | 🚒 **Fire & Rescue Dept** | 🚔 Police Control Room | Thermal Coordinates, Hazard Footprint ($m^2$), Camera Node GPS, Timestamp |
| **Crowd Stampede / Panic Surge** | Fluid flow alignment ($\phi > 0.85$) + sudden acceleration | 🚔 **Police Control Room** | 🚑 Ambulance & EMS | Density Index ($\text{ppl}/m^2$), Exit Bottleneck Vector, Evacuation Routing |
| **Criminal / Wanted Suspect Hit** | ArcFace 512-d embedding match (cosine dist $< 0.35$) | 🚔 **Police Special Cell** | — | Suspect ID, Confidence Score, Camera Node GPS, Timestamp |
| **Hit-and-Run Evasion** | Crash detected + Vehicle observed exiting frame | 🚔 **Police Control Room** | 🚦 Traffic Dept | Fleeing Plate Number, Next Intercept Camera, Velocity Estimate (km/h) |

---

## Cross-Camera Correlation & Corridor Tracking Architecture

The **Cross-Camera Vehicle Tracker** (`cross_camera.py`) tracks vehicles across disjoint camera zones **without requiring second-stage GPU vision passes**, achieving microsecond-level query speeds:

1. **Spatial Geocoding**: Each camera node has calibrated coordinates $(\text{lat}_1, \text{lon}_1)$ and $(\text{lat}_2, \text{lon}_2)$.
2. **Haversine Distance**:
   $$\Delta \sigma = 2 \arcsin \sqrt{\sin^2\left(\frac{\Delta \text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta \text{lon}}{2}\right)}$$
   $$d = R \cdot \Delta \sigma \quad (\text{where } R = 6371 \text{ km})$$
3. **Corridor Velocity & Interception**:
   $$v_{\text{est}} = \frac{d}{\Delta t} \times 3600 \quad (\text{km/h})$$
   If $v_{\text{est}} \le 140\text{ km/h}$ and $d \le 25\text{ km}$, the sighting is correlated as a confirmed journey corridor. The system automatically computes the **nearest downstream camera node** to suggest physical interception checkpoints for law enforcement.

---

## Hardware Sizing & Scalability Calculations

The following table provides hardware sizing and throughput calculations across three deployment scales: **30 Cameras** (Hackathon Pilot), **50 Cameras** (District Urban Hub), and **80,000 Cameras** (Statewide Gujarat Safe City Command):

| System Parameter | 30 Cameras (Current Pilot) | 50 Cameras (District Hub) | 80,000 Cameras (Statewide Gujarat Grid) |
|---|---|---|---|
| **Target Video Resolution** | 1080p @ 25 FPS (H.264/H.265) | 1080p @ 25 FPS (H.264/H.265) | 1080p @ 15–25 FPS Dynamic Adaptive |
| **Aggregate Frame Ingestion Rate** | 750 FPS (1.55 GPixels/sec) | 1,250 FPS (2.59 GPixels/sec) | 1,600,000 FPS (3,317 GPixels/sec) |
| **Network Ingestion Bandwidth** | ~120 Mbps (TCP RTSP) | ~200 Mbps (TCP RTSP) | ~320 Gbps Aggregate (Edge-Aggregated) |
| **Recommended GPU Compute** | 1× NVIDIA Quadro RTX 5000 / RTX 4080 | 1× NVIDIA A100 (40GB) or 2× RTX 4090 | Distributed Cluster: ~600–800× NVIDIA L40S / A100 Nodes |
| **GPU VRAM Utilization** | ~3.4 GB / 16 GB GDDR6 | ~7.8 GB / 40 GB HBM2 | ~16–24 GB per Edge Compute Node |
| **Inference Engine Optimization** | PyTorch FP16 TensorRT Engine | TensorRT FP16 / INT8 Quantized | INT8 TensorRT + DeepStream Pipeline |
| **Host CPU Architecture** | 8 Cores / 16 Threads (x86_64) | 16 Cores / 32 Threads (AMD EPYC) | 64-Core AMD EPYC Nodes (Edge Clusters) |
| **System Host RAM** | 32 GB DDR4/DDR5 | 64 GB DDR5 | 128 GB–256 GB ECC RAM per Node |
| **Queueing Architecture** | In-Memory Lossy-Drop FIFO (`frame_queue.py`) | Redis Cluster (In-Memory Ring Buffer) | Distributed Apache Kafka (Partitioned per District) |
| **Queue Buffer Depth & Latency** | Max 120 Frames (<25ms Latency) | Max 500 Frames (<25ms Latency) | Multi-Tier Partitioned (<40ms E2E Latency) |
| **Database Architecture** | Supabase Cloud PostgreSQL + Local Fallback | PostgreSQL 16 + PostGIS + pgvector | Distributed Citus PostGIS Cluster + ScyllaDB Time-Series |
| **Database Write Throughput** | ~40–80 Transactions/sec | ~120–250 Transactions/sec | ~25,000–50,000 Batched Events/sec |
| **Vector Search Capacity (pgvector)** | 10,000 Wanted Face Embeddings | 100,000 Criminal Embeddings | 10,000,000+ Embeddings (HNSW Graph Index) |
| **Cold Video Archive Tier** | Local SSD Cache / NVMe (48 Hours) | 10 TB NVMe + 50 TB NAS | Multi-Petabyte Ceph Object Store / S3 Glacier |
| **Emergency Dispatch Latency** | < 50ms Webhook / In-Memory Broadcast | < 50ms Webhook / MQ Alert | < 100ms Guaranteed Multi-Agency SLA |

---

## Federated Role-Based Access Control (Model 3)

```mermaid
flowchart LR
    classDef src fill:#ECEFF1,stroke:#546E7A,stroke-width:2px,color:#263238;
    classDef gw fill:#FCE4EC,stroke:#C2185B,stroke-width:2px,color:#880E4F;
    classDef dept fill:#E0F2F1,stroke:#00796B,stroke-width:2px,color:#004D40;

    SupaEvents["☁️ Supabase / Incident-Based Event Backbone\nStores ONLY Incident & Watchlist Triggers"]:::src --> GW["🛡️ FastAPI Gateway (`server.py`)\nJWT Token Validation + Dynamic RBAC Filter"]:::gw

    GW -->|POLICE_ADMIN Role| P["🚔 Police Control Room\n✅ Face Recognition & Criminal Watchlists\n✅ Stolen Vehicles & Corridor Intercepts\n✅ Full RTSP Camera Matrix Feeds\n✅ Automated Incident Dispatch Alerts"]:::dept

    GW -->|TRAFFIC_DEPT Role| T["🚦 Traffic Department\n✅ ANPR License Plates & Vehicle Counts\n✅ Accident Detection & Congestion Metrics\n🔒 Criminal Watchlists Masked\n🔒 Face Recognition Vectors Stripped"]:::dept

    GW -->|MUNICIPAL Role| M["🏛️ Municipal / City Corporation\n✅ Crowd Flow Dynamics & Density Heatmaps\n✅ Fire & Hazard Detection Alerts\n✅ GIS Infrastructure Nodes\n🔒 Vehicle Plates & Person Identities Stripped"]:::dept
```

---

## Technology Stack

| Layer | Component | Official Suggested Tech | Sentinel Implementation |
|---|---|---|---|
| **Ingestion & Streaming** | RTSP / ONVIF / WebRTC | RTSP libraries / WebRTC / HLS relay | Concurrent StreamGrabber (`stream_grabber.py`) + Low-Latency MJPEG over TCP |
| **Messaging & Queue** | In-Memory Frame Bus | Kafka / RabbitMQ / Redis | High-Speed Frame Queue (`frame_queue.py`) with Lossy-Drop (<25ms Latency) |
| **Base AI / ML Engine** | Object Detection & Tracking | YOLOv8 / Open-source Vision Models | YOLOv8x + ByteTrack with CUDA 11.8 FP16 acceleration |
| **ANPR Subsystem** | OCR & Plate Extraction | ANPR custom/open models | EasyOCR with Grayscale Bilateral Filter + Morphological Contrast Prep |
| **Corridor Correlator** | Cross-Camera Journey Map | Spatial-temporal correlation | `CrossCameraVehicleTracker` (`cross_camera.py`) with Haversine velocity |
| **Crash & Hazard Engine** | Kinematic Crash / Fire | Motion & Thermal Analytics | `AccidentDetector` (`models/accident_detection.py`) + Hazard analyzer |
| **Crowd Flow Engine** | Crowd Density & Dynamics | Fluid-dynamics approximation | `CrowdFlowAnomalyDetector` (`models/crowd_flow.py`) CPU-only vector math |
| **Emergency Dispatch** | Multi-Agency Notification | Webhooks / Microservice Callouts | Guarded `EmergencyDispatcher` (`alert_dispatcher.py`) (Police, Fire, EMS) |
| **Database & GIS** | Event Store, Vectors & GIS | PostgreSQL + PostGIS | Supabase PostgreSQL + PostGIS GIS Registry + pgvector + Offline Fallback |
| **Middleware & Gateway** | Federated API & RBAC | Node.js / Python (FastAPI/Django) | Python FastAPI Microservices (`server.py`) + JWT Department-Wise RBAC |
| **Frontend Interface** | Multi-Dept Tactical HUD | React.js | **React 19 SPA (Vite + Tailwind CSS + Lucide Icons + JetBrains Mono)** |
| **GIS Mapping** | Tactical Map Visualization | Leaflet / OpenLayers | **Native Leaflet.js with Inverted Dark OpenStreetMap Tiles (100% Free, Zero Watermarks)** |
| **Containerization** | Production Packaging | Docker / Compose | Multi-Service Docker Compose (CUDA 11.8 Passthrough + Dev Mode Frontend) |

---

## Database Schema — 9 Tables

| # | Table | Purpose |
|---|---|---|
| 1 | `camera_locations` | GIS Registry — 30 Geocoded Gujarat Camera Nodes (Ahmedabad, Junagadh, Navsari, Rajkot, etc.) |
| 2 | `ai_events` | Central Event Backbone — Incident-based triggers, timestamps, and alert severity |
| 3 | `log_people` | Capability 1 & 11: Crowd count, density index, and fluid-flow velocity metrics |
| 4 | `log_vehicles` | Capability 2 & 4: Vehicle records (**INCIDENT-BASED ONLY** — saved if involved in a crash, violation, or anomaly) |
| 5 | `log_license_plates` | Capability 3: ANPR records (**INCIDENT-BASED ONLY** — NOT mass surveillance; logged only if speeding, stolen, or flagged) |
| 6 | `log_objects` | Capability 5: Abandoned or unattended suspicious objects with stationary timer |
| 7 | `log_activities` | Capability 6: Suspicious human behaviors (running, loitering, violent fighting) |
| 8 | `watchlist_vehicles` | Capability 8 & 9: Stolen / flagged vehicles with active APB broadcast records |
| 9 | `watchlist_faces` | Capability 7: Wanted persons and missing individuals with ArcFace 512-d embeddings |

---

## Cyber Command Interface Architecture

```mermaid
flowchart TD
    classDef main fill:#0A0E17,stroke:#00F3FF,stroke-width:2px,color:#00F3FF;
    classDef tab fill:#111827,stroke:#0066FF,stroke-width:2px,color:#E0F2FE;
    classDef feature fill:#1F2937,stroke:#FFB800,stroke-width:2px,color:#FEF3C7;
    classDef alert fill:#371B1B,stroke:#FF003C,stroke-width:2px,color:#FECACA;

    Hub["🛡️ Sentinel Tactical Command Center (Cyber HUD)"]:::main

    Hub --> T1["Tab 1: Tactical Camera Matrix Grid"]:::tab
    Hub --> T2["Tab 2: Gujarat Tactical GIS Map"]:::tab
    Hub --> T3["Tab 3: Target Scanner & AI Focus View"]:::tab
    Hub --> T4["Tab 4: Central Command 'God Mode'"]:::tab

    T1 --> F1["- Simultaneous Live Video Feeds\n- Independent RTSP Workers over TCP (No Bleed)\n- Instant Search & District Filters\n- One-Click Camera Activation"]:::feature
    T2 --> F2["- Dark Tactical Inverted OpenStreetMap Tiles\n- 30 Geocoded Nodes across Gujarat\n- Dynamic Radar Pulse Wave Animations\n- Node Status: Normal / Connecting / Alert"]:::feature
    T3 --> F3["- Full-Resolution Camera Viewport\n- Live Cyan Laser Scanning Animation\n- Real-Time OCR Plate Extraction & Vehicle Color\n- Cross-Camera Corridor Journey Search"]:::feature
    F3 --> A1["🚨 Red Siren Alert on Stolen Vehicle or Wanted Hit"]:::alert
    T4 --> F4["- Central Video Feed + Live Status Strip\n- 8-Stage Vision Pipeline Status Display\n- Real-Time Scrolling Audit Log (<25ms)\n- Department RBAC Clearance Indicators"]:::feature
```
